import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class AuthService {
  final String baseUrl = 'http://192.168.0.154:5000'; // or localhost

  String? _cookie;

  Future<bool> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final rawCookie = response.headers['set-cookie'];
      if (rawCookie != null) {
        _cookie = rawCookie.split(';').first;
      }
      return true;
    } else {
      return false;
    }
  }

  Future<bool> signup(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/signup'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    return response.statusCode == 200;
  }

  Future<Map<String, dynamic>> analyzeImage(File image) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/analyze'));
    request.files.add(await http.MultipartFile.fromPath('image', image.path));

    if (_cookie != null) {
      request.headers['cookie'] = _cookie!;
    }

    var response = await request.send();
    var responseBody = await response.stream.bytesToString();
    if (response.statusCode == 200) {
      return jsonDecode(responseBody);
    } else {
      return {'error': 'Status ${response.statusCode}'};
    }
  }

  Future<String> testConnection() async {
    final url = Uri.parse('$baseUrl/');
    final response = await http.get(url);
    return 'Connection test: ${response.statusCode}';
  }

  Future<bool> logout() async {
    final response = await http.post(
      Uri.parse('$baseUrl/logout'),
      headers: {if (_cookie != null) 'cookie': _cookie!},
    );
    if (response.statusCode == 200) {
      _cookie = null; // Clear local cookie too
      return true;
    } else {
      return false;
    }
  }
}

// import 'dart:convert';
// import 'dart:io';
// import 'package:http/http.dart' as http;

// class AuthService {
//   final String baseUrl = 'http://192.168.0.154:5000'; // OR your local network IP for simulator
//   String? _cookie; // store the session cookie

//   Future<bool> login(String email, String password) async {
//     final response = await http.post(
//       Uri.parse('$baseUrl/login'),
//       body: {'email': email, 'password': password},
//     );

//     if (response.statusCode == 200) {
//       // ✅ Save the cookie from Set-Cookie header
//       final rawCookie = response.headers['set-cookie'];
//       if (rawCookie != null) {
//         _cookie = rawCookie.split(';').first;
//       }
//       return true;
//     } else {
//       return false;
//     }
//   }

//   Future<bool> signup(String email, String password) async {
//     final response = await http.post(
//       Uri.parse('$baseUrl/signup'),
//       body: {'email': email, 'password': password},
//     );

//     return response.statusCode == 200;
//   }

//   Future<Map<String, dynamic>> analyzeImage(File image) async {
//     final request = http.MultipartRequest(
//       'POST',
//       Uri.parse('$baseUrl/analyze'),
//     );
//     request.files.add(await http.MultipartFile.fromPath('image', image.path));

//     if (_cookie != null) {
//       request.headers['cookie'] = _cookie!;
//     }

//     final streamedResponse = await request.send();
//     final response = await http.Response.fromStream(streamedResponse);

//     if (response.statusCode == 401) {
//       return {
//         'error': 'Unauthorized: Please log in first.'
//       };
//     }

//     return jsonDecode(response.body);
//   }
// }
