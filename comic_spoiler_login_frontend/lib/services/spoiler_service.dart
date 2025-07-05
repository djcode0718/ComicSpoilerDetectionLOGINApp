import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';

class SpoilerService {
  final String baseUrl = 'http://192.168.0.154:5000';

  Future<Map<String, dynamic>> analyzeImage(File image) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/analyze'));
    request.files.add(await http.MultipartFile.fromPath('image', image.path));
    var response = await request.send();
    var responseData = await http.Response.fromStream(response);
    return jsonDecode(responseData.body);
  }
}
