import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../models/models.dart';

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
  Future<Uint8List?> fetchProducts({
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
            Uri.parse('$baseUrl/fetch-products?excel=true'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        return response.bodyBytes;
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
