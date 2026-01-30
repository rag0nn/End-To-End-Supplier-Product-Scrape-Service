import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';

/// API Response
class ApiResponse {
  final List<Product> successedProducts;
  final List<Product> failedProducts;

  ApiResponse({
    required this.successedProducts,
    required this.failedProducts,
  });
}

/// Remote sunucu ile iletişim servisi
class ApiService {
  final String baseUrl;
  final http.Client _client;

  ApiService({required this.baseUrl, http.Client? client})
      : _client = client ?? http.Client();

  /// Sunucu sağlık kontrolü
  Future<bool> healthCheck() async {
    try {
      final response = await _client
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Ürünleri sunucudan çek
  Future<ApiResponse?> fetchProducts({
    required List<PreState> prestates,
    required Supplier supplier,
  }) async {
    // Önce health check
    final isHealthy = await healthCheck();
    if (!isHealthy) {
      return null;
    }

    try {
      final payload = {
        'prestates': prestates.map((p) => p.toJson()).toList(),
        'supplier': supplier.prefix,
      };

      final response = await _client
          .post(
            Uri.parse('$baseUrl/fetch-products'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        final successedProducts = <Product>[];
        final failedProducts = <Product>[];

        // Başarılı ürünleri parse et
        final successedData = data['successed'];
        if (successedData != null && successedData['products'] != null) {
          for (var item in successedData['products']) {
            successedProducts.add(Product.fromSerialized(item));
          }
        }

        // Başarısız ürünleri parse et
        final failedData = data['failed'];
        if (failedData != null && failedData['products'] != null) {
          for (var item in failedData['products']) {
            failedProducts.add(Product.fromSerialized(item));
          }
        }

        return ApiResponse(
          successedProducts: successedProducts,
          failedProducts: failedProducts,
        );
      }

      return null;
    } catch (e) {
      return null;
    }
  }

  void dispose() {
    _client.close();
  }
}
