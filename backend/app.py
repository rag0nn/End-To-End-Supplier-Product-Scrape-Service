import os
import logging
from typing import List
from supplier_scrape_core.processer import Processer
from supplier_scrape_core.structers.product import Suppliers,PreState
from flask import Flask, request, jsonify

# app initialize
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 16 * 1024 # 16 MB max request size

# # logs
# logging = logging.getlogging(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def create_prestate_objects_from_list(prestate_data: List[dict]) -> List[PreState]:
    prestates = []
    for item in prestate_data:
        try:
            prestate = PreState.from_dict(item)
            prestates.append(prestate)
        except (KeyError, TypeError) as e:
            logging.error(f"PreState build error: {e}")
            continue
    return prestates

@app.route('/health', methods=['GET'])
def health_check():
    """Sunucunu sağlık durumunu kontrol et"""
    return jsonify({
        "status" : "ok",
        "message" : "Server is running"
    }), 200
    
@app.route('/fetch-products', methods=["POST"])
def fetch_products():
    """
    Docstring for fecth_products
    """
    try:
        data = request.get_json()
        
        if not data:
            response_text = "Request body has zero items"
            logging.error(response_text)
            return jsonify({"error", response_text})
        
        # prestate text listesini al
        prestate_texts = data.get('prestates',[])
        if not prestate_texts or not isinstance(prestate_texts,list):
            response_text = "Unvalid body prestates text format"
            logging.error(response_text)
            return jsonify({"error": response_text})
        
        # prestate objelerini oluştur 
        prestates = create_prestate_objects_from_list(prestate_texts)
        if not prestates:
            response_text =  "Prestate objects could'nt build"
            logging.error(response_text)
            return jsonify("error",response_text)
        
        # supplierı al
        supplier_code = data.get('supplier', None)
        if not supplier_code:
            response_text = "Could'nt reach the supplier"
            logging.error(response_text)
            return jsonify("error",response_text)
        
        supplier = None
        for sup in Suppliers:
            if sup.value["prefix"] == supplier_code:
                supplier = sup
                break
        
        # text'ten supplier'ı oluştur
        if not supplier:
            response_text = f"Invalid supplier code. Input: {supplier_code}"
            logging.error(response_text)
            return jsonify("error",response_text)
        
        # Ürünleri işle
        processer = Processer()
        logging.info(f"Products will fetch using {supplier.name}")
        prodducts_successed, products_failed = processer.get_with_code(supplier,*prestates)
        
        # ürünleri serialize et
        serialized_successed = [product.serialize() for product in prodducts_successed]
        serialized_failed = [product.serialize() for product in products_failed]
        
        # response
        response = {
            "successed" : {
                "count" : len(serialized_successed),
                "products" : serialized_successed
            },
            "failed" : {
                "count" : len(serialized_failed),
                "products" : serialized_failed
            }
        }
        return jsonify(response), 200
    
    except Exception as e:
        response_text = f"Unknown process fail: {e}"
        logging.error(response_text)
        return jsonify({"error" : response_text}), 500
    
@app.errorhandler(404)
def not_found(error):
    """404 hatası"""
    return jsonify({"error": "Endpoint could'nt find"}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 hatası"""
    return jsonify({"error": "Server fail"}), 500       

if __name__ == "__main__":
    logging.info("Server Starting...")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
    
        

        
            
    