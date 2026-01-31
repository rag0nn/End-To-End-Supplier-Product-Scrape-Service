import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:open_filex/open_filex.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // Form controllers
  final _productCodeController = TextEditingController();
  final _priceController = TextEditingController();

  // State
  Supplier _selectedSupplier = Supplier.balgunes;
  int _quantity = 1;
  final List<ProductRow> _productRows = [];
  bool _isLoading = false;
  String? _lastExcelPath;

  // Settings
  static const String _remoteUrlKey = 'remote_url';
  static const String _defaultUrl = 'http://192.168.1.20:5000';
  String _remoteUrl = _defaultUrl;

  // Services
  late ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _remoteUrl = prefs.getString(_remoteUrlKey) ?? _defaultUrl;
      _apiService = ApiService(baseUrl: _remoteUrl);
    });
  }

  Future<void> _saveRemoteUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_remoteUrlKey, url);
    setState(() {
      _remoteUrl = url;
      _apiService.dispose();
      _apiService = ApiService(baseUrl: _remoteUrl);
    });
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: _remoteUrl);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Ayarlar'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Sunucu URL',
            hintText: 'http://192.168.1.20:5000',
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.url,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('İptal'),
          ),
          ElevatedButton(
            onPressed: () {
              _saveRemoteUrl(controller.text.trim());
              Navigator.pop(context);
              _showSuccess('Ayarlar kaydedildi');
            },
            child: const Text('Kaydet'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _productCodeController.dispose();
    _priceController.dispose();
    _apiService.dispose();
    super.dispose();
  }

  /// Kaydedilen son dosya konumunu aç
  Future<void> _openLastExcelLocation() async {
    final path = _lastExcelPath;
    if (path == null) {
      _showError('Henüz kaydedilmiş bir dosya yok');
      return;
    }

    try {
      if (Platform.isWindows) {
        // Windows: Explorer ile dosyayı seçili olarak aç
        // Not: 'explorer.exe' ve '/select,' argümanı dosyanın olduğu klasörü açar ve dosyayı seçer
        await Process.run('explorer.exe', ['/select,', path]);
      } else if (Platform.isAndroid || Platform.isIOS) {
        // Mobile: Dosyayı direkt aç (Klasör açmak genelde desteklenmez veya kullanıcı dostu değildir)
        final result = await OpenFilex.open(path);
        if (result.type != ResultType.done) {
          _showError('Dosya açılamadı: ${result.message}');
        }
      } else {
        _showError(
          'Bu özellik şu an sadece Windows ve Mobil platformlarda destekleniyor.',
        );
      }
    } catch (e) {
      _showError('Konum açılırken hata: $e');
    }
  }

  /// Tabloya ürün ekle
  void _addProductToTable() {
    // Validasyon
    final productCode = int.tryParse(_productCodeController.text);
    final price = int.tryParse(_priceController.text);

    if (productCode == null) {
      _showError(
        _productCodeController.text.isEmpty
            ? 'Ürün kodu mutlaka girilmelidir'
            : 'Ürün kodu sadece sayı içermelidir',
      );
      return;
    }

    if (price == null) {
      _showError(
        _priceController.text.isEmpty
            ? 'Ürün fiyatı mutlaka girilmelidir'
            : 'Ürün fiyatı sadece sayı içermelidir',
      );
      return;
    }

    setState(() {
      _productRows.add(
        ProductRow(
          supplier: _selectedSupplier,
          productCode: productCode,
          price: price,
          quantity: _quantity,
        ),
      );
    });

    // Formu temizle
    _productCodeController.clear();
    _priceController.clear();

    // Klavyeyi kapat
    FocusScope.of(context).unfocus();
  }

  /// Ürünleri sunucuya gönder
  Future<void> _sendProducts() async {
    if (_productRows.isEmpty) {
      _showError('Tabloya herhangi bir öğe eklenmemiş');
      return;
    }

    setState(() => _isLoading = true);

    try {
      // Tedarikçilere göre grupla
      final Map<Supplier, List<ProductRow>> groupedProducts = {};
      for (var supplier in Supplier.values) {
        groupedProducts[supplier] = [];
      }
      for (var row in _productRows) {
        groupedProducts[row.supplier]!.add(row);
      }

      // Her tedarikçi için ayrı istek gönder
      for (var entry in groupedProducts.entries) {
        final supplier = entry.key;
        final rows = entry.value;

        if (rows.isEmpty) continue;

        final prestates = rows.map((r) => r.toPreState()).toList();
        final responseBytes = await _apiService.fetchProducts(
          prestates: prestates,
          supplier: supplier,
        );

        if (responseBytes == null) {
          _showError(
            'Sunucuya bağlanılamadı veya hata oluştu (${supplier.displayName})',
          );
          // Hata durumunda diğer tedarikçilere devam edebiliriz veya durabiliriz.
          // Burada devam etmeyelim.
          continue;
        }

        // Excel dosyasını kaydet
        Directory? directory;
        if (Platform.isAndroid) {
          directory = await getExternalStorageDirectory();
        }

        // Android'de external storage başarısız olursa veya diğer platformlarda documents klasörü
        directory ??= await getApplicationDocumentsDirectory();

        final fileName =
            'products_${supplier.displayName}_${DateTime.now().millisecondsSinceEpoch}.xlsx';
        final path = '${directory.path}/$fileName';
        final file = File(path);

        await file.writeAsBytes(responseBytes);
        _lastExcelPath = path;

        // Başarılı kabul et ve satırları güncelle
        for (var row in rows) {
          row.success = true;
        }
      }

      setState(() {});
      _showSuccess(
        'Ürünler işlem gördü ve dosya kaydedildi.${_lastExcelPath != null ? '\nSon Dosya: $_lastExcelPath' : ''}',
      );
    } catch (e) {
      _showError('İşlem sırasında hata oluştu: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 4),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Ürün Kazıyıcı'),
        centerTitle: true,
        elevation: 2,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Ayarlar',
            onPressed: _showSettingsDialog,
          ),
          IconButton(
            icon: const Icon(Icons.folder_open),
            tooltip: 'Dosya Konumunu Aç',
            onPressed: _openLastExcelLocation,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Form alanları - Scrollable
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Form kartı
                    _buildForm(),
                    const SizedBox(height: 16),

                    // Ürün listesi
                    _buildProductList(),
                  ],
                ),
              ),
            ),

            // Gönder butonu - Altta sabit
            _buildSendButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildForm() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Tedarikçi Dropdown
            DropdownButtonFormField<Supplier>(
              initialValue: _selectedSupplier,
              decoration: const InputDecoration(
                labelText: 'Tedarikçi Kodu',
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 12,
                ),
              ),
              items: Supplier.values.map((s) {
                return DropdownMenuItem(
                  value: s,
                  child: Text('${s.prefix} ${s.displayName}'),
                );
              }).toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() => _selectedSupplier = value);
                }
              },
            ),
            const SizedBox(height: 12),

            // Ürün Kodu ve Fiyat - Yan yana
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _productCodeController,
                    decoration: const InputDecoration(
                      labelText: 'Ürün Kodu',
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                    ),
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _priceController,
                    decoration: const InputDecoration(
                      labelText: 'Fiyat',
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                    ),
                    keyboardType: TextInputType.number,
                    inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Adet ve Ekle butonu
            Row(
              children: [
                // Adet kontrolü
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text('Adet: ', style: TextStyle(fontSize: 14)),
                        IconButton(
                          icon: const Icon(Icons.remove_circle_outline),
                          onPressed: _quantity > 1
                              ? () => setState(() => _quantity--)
                              : null,
                          iconSize: 28,
                          color: Colors.red,
                        ),
                        Text(
                          '$_quantity',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.add_circle_outline),
                          onPressed: _quantity < 100
                              ? () => setState(() => _quantity++)
                              : null,
                          iconSize: 28,
                          color: Colors.green,
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                // Ekle Butonu
                SizedBox(
                  height: 48,
                  child: ElevatedButton.icon(
                    onPressed: _addProductToTable,
                    icon: const Icon(Icons.add),
                    label: const Text('Ekle'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProductList() {
    if (_productRows.isEmpty) {
      return Card(
        elevation: 2,
        child: Container(
          height: 150,
          alignment: Alignment.center,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.inbox_outlined, size: 48, color: Colors.grey[400]),
              const SizedBox(height: 8),
              Text(
                'Henüz ürün eklenmedi',
                style: TextStyle(color: Colors.grey[600], fontSize: 16),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      elevation: 2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Text(
              'Ürünler (${_productRows.length})',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
          ),
          const Divider(height: 1),
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _productRows.length,
            separatorBuilder: (context, index) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final row = _productRows[index];
              return ListTile(
                dense: true,
                leading: CircleAvatar(
                  radius: 18,
                  backgroundColor: Colors.blue.shade100,
                  child: Text(
                    row.supplier.prefix,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.blue.shade800,
                    ),
                  ),
                ),
                title: Text(
                  'Kod: ${row.productCode}',
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
                subtitle: Text(
                  'Fiyat: ${row.price} TL • Adet: ${row.quantity}',
                ),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _buildStatusIcon(row.success),
                    IconButton(
                      icon: const Icon(Icons.delete_outline, color: Colors.red),
                      onPressed: () {
                        setState(() => _productRows.removeAt(index));
                      },
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildStatusIcon(bool? success) {
    if (success == null) {
      return const SizedBox(width: 24);
    }
    return Icon(
      success ? Icons.check_circle : Icons.cancel,
      color: success ? Colors.green : Colors.red,
      size: 24,
    );
  }

  Widget _buildSendButton() {
    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withAlpha(50),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SizedBox(
        width: double.infinity,
        height: 50,
        child: ElevatedButton(
          onPressed: _isLoading ? null : _sendProducts,
          style: ElevatedButton.styleFrom(
            backgroundColor: Theme.of(context).primaryColor,
            foregroundColor: Colors.white,
          ),
          child: _isLoading
              ? const SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(
                    color: Colors.white,
                    strokeWidth: 2,
                  ),
                )
              : const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.send),
                    SizedBox(width: 8),
                    Text('Gönder', style: TextStyle(fontSize: 18)),
                  ],
                ),
        ),
      ),
    );
  }
}
