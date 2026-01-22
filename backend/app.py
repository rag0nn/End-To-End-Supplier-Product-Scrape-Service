import logging
import io
import os
from typing import List, Tuple
from flask import Flask, request, jsonify, send_file
from supplier_scrape_core.processer import Processer, SaverLikeIkasTemplate
from supplier_scrape_core.structers.product import Suppliers, PreState

# Flask uygulaması oluştur
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Logging konfigürasyonu
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[41m", # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{color}{message}{self.RESET}"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)

# Sabit değerler
STATIC_VALUES = {
    "Satış Kanalı:nurcocuk": "VISIBLE",
    "Tip": "PHYSICAL"
}


def create_prestates_from_list(data: List[dict]) -> List[PreState]:
    """
    Dictionary listesinden PreState nesneleri oluştur
    
    Args:
        data: [{code, price, stock}, ...] formatında liste
        
    Returns:
        PreState nesneleri listesi
    """
    prestates = []
    for item in data:
        try:
            prestate = PreState(
                code=item.get('code'),
                price=item.get('price'),
                stock=item.get('stock')
            )
            prestates.append(prestate)
        except (KeyError, TypeError) as e:
            logger.warning(f"PreState oluşturma hatası: {e}")
            continue
    return prestates


@app.route('/api/health', methods=['GET'])
def health_check():
    """Sunucunun sağlık durumunu kontrol et"""
    return jsonify({
        "status": "ok",
        "message": "Server çalışıyor"
    }), 200


@app.route('/api/process-products', methods=['POST'])
def process_products():
    """
    Ürünleri işle ve Excel dosyalarını döndür
    
    Request body:
    {
        "prestates": [
            {"code": 145204, "price": 30, "stock": 12},
            {"code": 147149, "price": 50, "stock": 10},
            ...
        ],
        "supplier": "BALGUNES",  # Optional, default: BALGUNES
        "static_values": {...}    # Optional, default: STATIC_VALUES
    }
    
    Returns:
        - Success (200): Excel dosyalarını zip olarak döndür
        - Error (400/500): Hata mesajı
    """
    try:
        # Request body'yi al
        data = request.get_json()
        
        if not data:
            logger.error("Request body boş")
            return jsonify({"error": "Request body boş"}), 400
        
        # PreState listesini al
        prestates_data = data.get('prestates', [])
        if not prestates_data or not isinstance(prestates_data, list):
            logger.error("Geçersiz prestates formatı")
            return jsonify({"error": "prestates: array formatında olmalı"}), 400
        
        # PreState nesneleri oluştur
        prestates = create_prestates_from_list(prestates_data)
        if not prestates:
            logger.error("PreState oluşturulamadı")
            return jsonify({"error": "Geçerli PreState bulunamadı"}), 400
        
        logger.info(f"{len(prestates)} ürün işlenecek")
        
        # Supplier'ı al (default: BALGUNES)
        supplier_name = data.get('supplier', 'BALGUNES')
        try:
            supplier = Suppliers[supplier_name]
        except KeyError:
            logger.error(f"Geçersiz supplier: {supplier_name}")
            return jsonify({
                "error": f"Geçersiz supplier. Kullanılabilir: {[s.name for s in Suppliers]}"
            }), 400
        
        # Static values'ı al
        static_values = data.get('static_values', STATIC_VALUES)
        
        # Ürünleri işle
        processer = Processer()
        logger.info(f"Ürünler {supplier.name} üzerinden çekiliyor...")
        products, failed_products = processer.get_with_code(supplier, *prestates)
        
        logger.info(f"Başarılı: {len(products)}, Başarısız: {len(failed_products)}")
        
        # Excel dosyalarını bellek içinde oluştur
        saver = SaverLikeIkasTemplate()
        
        # Success Excel
        success_buffer = io.BytesIO()
        saver.fill(products, static_values, success_buffer)
        success_buffer.seek(0)
        
        # Failed Excel
        failed_buffer = io.BytesIO()
        saver.fill(failed_products, static_values, failed_buffer)
        failed_buffer.seek(0)
        
        # Response olarak gönder (success.xlsx olarak)
        # İlk başta success dosyasını gönder
        response = send_file(
            success_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='success.xlsx'
        )
        
        # Header'a bilgi ekle
        response.headers['X-Success-Count'] = str(len(products))
        response.headers['X-Failed-Count'] = str(len(failed_products))
        
        logger.info("Excel dosyaları başarıyla oluşturuldu")
        
        return response
        
    except Exception as e:
        logger.error(f"İşleme hatası: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"İşleme hatası: {str(e)}"
        }), 500


@app.route('/api/process-products-zip', methods=['POST'])
def process_products_zip():
    """
    Ürünleri işle ve her iki Excel dosyasını ZIP olarak döndür
    
    Request body:
    {
        "prestates": [
            {"code": 145204, "price": 30, "stock": 12},
            {"code": 147149, "price": 50, "stock": 10},
            ...
        ],
        "supplier": "BALGUNES",  # Optional
        "static_values": {...}    # Optional
    }
    
    Returns:
        - Success (200): ZIP dosyası (success.xlsx + failed.xlsx)
        - Error (400/500): Hata mesajı
    """
    try:
        import zipfile
        
        # Request body'yi al
        data = request.get_json()
        
        if not data:
            logger.error("Request body boş")
            return jsonify({"error": "Request body boş"}), 400
        
        # PreState listesini al
        prestates_data = data.get('prestates', [])
        if not prestates_data or not isinstance(prestates_data, list):
            logger.error("Geçersiz prestates formatı")
            return jsonify({"error": "prestates: array formatında olmalı"}), 400
        
        # PreState nesneleri oluştur
        prestates = create_prestates_from_list(prestates_data)
        if not prestates:
            logger.error("PreState oluşturulamadı")
            return jsonify({"error": "Geçerli PreState bulunamadı"}), 400
        
        logger.info(f"{len(prestates)} ürün işlenecek")
        
        # Supplier'ı al
        supplier_name = data.get('supplier', 'BALGUNES')
        try:
            supplier = Suppliers[supplier_name]
        except KeyError:
            logger.error(f"Geçersiz supplier: {supplier_name}")
            return jsonify({
                "error": f"Geçersiz supplier. Kullanılabilir: {[s.name for s in Suppliers]}"
            }), 400
        
        # Static values'ı al
        static_values = data.get('static_values', STATIC_VALUES)
        
        # Ürünleri işle
        processer = Processer()
        logger.info(f"Ürünler {supplier.name} üzerinden çekiliyor...")
        products, failed_products = processer.get_with_code(supplier, *prestates)
        
        logger.info(f"Başarılı: {len(products)}, Başarısız: {len(failed_products)}")
        
        # Excel dosyalarını bellek içinde oluştur
        saver = SaverLikeIkasTemplate()
        
        # Success Excel
        success_buffer = io.BytesIO()
        saver.fill(products, static_values, success_buffer)
        success_buffer.seek(0)
        
        # Failed Excel
        failed_buffer = io.BytesIO()
        saver.fill(failed_products, static_values, failed_buffer)
        failed_buffer.seek(0)
        
        # ZIP dosyası oluştur
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('success.xlsx', success_buffer.getvalue())
            zip_file.writestr('failed.xlsx', failed_buffer.getvalue())
        
        zip_buffer.seek(0)
        
        response = send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='products.zip'
        )
        
        # Header'a bilgi ekle
        response.headers['X-Success-Count'] = str(len(products))
        response.headers['X-Failed-Count'] = str(len(failed_products))
        
        logger.info("ZIP dosyası başarıyla oluşturuldu")
        
        return response
        
    except Exception as e:
        logger.error(f"İşleme hatası: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"İşleme hatası: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404 hatası"""
    return jsonify({"error": "Endpoint bulunamadı"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 hatası"""
    return jsonify({"error": "Sunucu hatası"}), 500


if __name__ == "__main__":
    # Çıkış dizinini oluştur
    os.makedirs("./output", exist_ok=True)
    
    logger.info("Flask servisi başlatılıyor...")
    logger.info("Endpoint'ler:")
    logger.info("  - GET  /api/health")
    logger.info("  - POST /api/process-products (success.xlsx döner)")
    logger.info("  - POST /api/process-products-zip (success.xlsx + failed.xlsx ZIP olarak döner)")
    
    # Debug mode ile başlat (production'da False yapılmalı)
    app.run(debug=True, host='0.0.0.0', port=5000)
