import 'dart:io';
import 'package:excel/excel.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../models/models.dart';

/// Excel dosyası oluşturma ve kaydetme servisi
class ExcelService {
  // Statik değerler
  static const Map<String, String> staticValues = {
    'Satış Kanalı:nurcocuk': 'VISIBLE',
    'Tip': 'PHYSICAL',
  };

  // Excel sütun başlıkları
  static const List<String> columns = [
    'Ürün Grup ID',
    'Varyant ID',
    'İsim',
    'Açıklama',
    'Satış Fiyatı',
    'İndirimli Fiyatı',
    'Alış Fiyatı',
    'Barkod Listesi',
    'SKU',
    'Silindi mi?',
    'Marka',
    'Kategoriler',
    'Etiketler',
    'Resim URL',
    'Metadata Başlık',
    'Metadata Açıklama',
    'Slug',
    'Stok:Ana Depo',
    'Tip',
    'Varyant Tip 1',
    'Varyant Değer 1',
    'Varyant Tip 2',
    'Varyant Değer 2',
    'Desi',
    'HS Kod',
    'Birim Ürün Miktarı',
    'Ürün Birimi',
    'Satılan Ürün Miktarı',
    'Satılan Ürün Birimi',
    'Google Ürün Kategorisi',
    'Tedarikçi',
    'Stoğu Tükenince Satmaya Devam Et',
    'Satış Kanalı:nurcocuk',
    'Sepet Başına Minimum Alma Adeti:nurcocuk',
    'Sepet Başına Maksimum Alma Adeti:nurcocuk',
    'Varyant Aktiflik',
  ];

  /// Ürünleri Excel dosyasına kaydet
  Future<File?> saveProducts({
    required List<Product> products,
    required String fileName,
  }) async {
    if (products.isEmpty) return null;

    try {
      final excel = Excel.createExcel();
      final sheetName = 'Ürünler';
      
      // Yeni sheet oluştur ve default sheet'i sil
      excel[sheetName];
      excel.delete('Sheet1');
      
      final sheet = excel[sheetName];

      // Başlık satırı
      for (var i = 0; i < columns.length; i++) {
        sheet
            .cell(CellIndex.indexByColumnRow(columnIndex: i, rowIndex: 0))
            .value = TextCellValue(columns[i]);
      }

      // Ürün satırları
      for (var rowIndex = 0; rowIndex < products.length; rowIndex++) {
        final product = products[rowIndex];
        
        // Değer haritası oluştur
        final Map<String, String> values = {
          'İsim': product.urunIsmi ?? '',
          'Açıklama': product.aciklama ?? '',
          'Satış Fiyatı': product.fiyat ?? '',
          'Barkod Listesi': product.urunKodu,
          'Kategoriler': product.kategori ?? '',
          'Resim URL': product.gorselUrl ?? '',
          'Stok:Ana Depo': product.stok ?? '',
          'Tip': staticValues['Tip']!,
          'Tedarikçi': product.marka?.prefix ?? '',
          'Satış Kanalı:nurcocuk': staticValues['Satış Kanalı:nurcocuk']!,
        };

        // Her sütun için değeri bul ve yaz
        for (var colIndex = 0; colIndex < columns.length; colIndex++) {
          final columnName = columns[colIndex];
          final value = values[columnName] ?? ''; // Eşleşen değer yoksa boş bırak
          
          if (value.isNotEmpty) {
             sheet
              .cell(CellIndex.indexByColumnRow(
                  columnIndex: colIndex, rowIndex: rowIndex + 1))
              .value = TextCellValue(value);
          }
        }
      }

      // Dosyayı kaydet
      final directory = await getApplicationDocumentsDirectory();
      final filePath = '${directory.path}/$fileName';
      final fileBytes = excel.save();

      if (fileBytes != null) {
        final file = File(filePath);
        await file.writeAsBytes(fileBytes);
        return file;
      }

      return null;
    } catch (e) {
      return null;
    }
  }

  /// Dosyayı paylaş (dışa aktar)
  Future<void> shareFile(File file) async {
    await Share.shareXFiles(
      [XFile(file.path)],
      subject: 'Ürün Listesi',
    );
  }

  /// Test amaçlı: Örnek ürünlerle Excel oluştur
  Future<File?> createTestExcel() async {
    final testProducts = [
      Product(
        urunKodu: '11175441',
        urunIsmi: 'Test Ürün 1',
        kategori: 'Bebek Giyim',
        gorselUrl: 'https://example.com/image1.jpg',
        fiyat: '350',
        stok: '10',
        aciklama: 'Test açıklama 1',
        marka: Supplier.balgunes,
      ),
      Product(
        urunKodu: '12444493',
        urunIsmi: 'Test Ürün 2',
        kategori: 'Çocuk Giyim',
        gorselUrl: 'https://example.com/image2.jpg',
        fiyat: '220',
        stok: '5',
        aciklama: 'Test açıklama 2',
        marka: Supplier.babexi,
      ),
    ];

    return saveProducts(
      products: testProducts,
      fileName: 'test_export_${DateTime.now().millisecondsSinceEpoch}.xlsx',
    );
  }
}
