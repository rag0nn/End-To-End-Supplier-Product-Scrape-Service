/// Tedarikçi enum'u - Backend ile aynı prefix değerlerini kullanır
enum Supplier {
  balgunes('11', 'BALGÜNEŞ'),
  babexi('12', 'BABEXI'),
  malkoc('13', 'MALKOÇ');

  final String prefix;
  final String displayName;

  const Supplier(this.prefix, this.displayName);

  /// Prefix'e göre tedarikçi bul
  static Supplier? fromPrefix(String prefix) {
    for (var supplier in Supplier.values) {
      if (supplier.prefix == prefix) {
        return supplier;
      }
    }
    return null;
  }
}

/// Ürün çekmeden önce gönderilecek ön bilgi
class PreState {
  final int code;
  final int price;
  final int stock;

  PreState({
    required this.code,
    required this.price,
    required this.stock,
  });

  Map<String, dynamic> toJson() {
    return {
      'code': code,
      'price': price,
      'stock': stock,
    };
  }
}

/// Sunucudan dönen ürün bilgisi
class Product {
  final String urunKodu;
  final String? urunIsmi;
  final String? kategori;
  final String? kategoriUrl;
  final String? gorselUrl;
  final String? fiyat;
  final String? stok;
  final String? aciklama;
  final String? puan;
  final Supplier? marka;

  Product({
    required this.urunKodu,
    this.urunIsmi,
    this.kategori,
    this.kategoriUrl,
    this.gorselUrl,
    this.fiyat,
    this.stok,
    this.aciklama,
    this.puan,
    this.marka,
  });

  /// Serialize edilmiş string'den Product oluştur
  /// Format: urun_kodu-urun_ismi-kategori-kategori_url-gorsel_url-fiyat-stok-aciklama-puan-marka_prefix
  factory Product.fromSerialized(String data) {
    final items = data.split('-');
    
    Supplier? marka;
    if (items.length > 10) {
      marka = Supplier.fromPrefix(items[10]);
    }

    return Product(
      urunKodu: items[0],
      urunIsmi: items.length > 1 ? items[1] : null,
      kategori: items.length > 2 ? items[2] : null,
      kategoriUrl: items.length > 3 ? items[3] : null,
      fiyat: items.length > 4 ? items[4] : null,
      stok: items.length > 5 ? items[5] : null,
      gorselUrl: items.length > 6 ? items[6] : null,
      aciklama: items.length > 8 ? items[8] : null,
      puan: items.length > 9 ? items[9] : null,
      marka: marka,
    );
  }



  @override
  String toString() {
    return 'Product(kodu: $urunKodu, ismi: $urunIsmi)';
  }
}

/// Tabloda gösterilecek ürün satırı
class ProductRow {
  final Supplier supplier;
  final int productCode;
  final int price;
  final int quantity;
  bool? success;

  ProductRow({
    required this.supplier,
    required this.productCode,
    required this.price,
    required this.quantity,
    this.success,
  });

  PreState toPreState() {
    return PreState(
      code: productCode,
      price: price,
      stock: quantity,
    );
  }
}
