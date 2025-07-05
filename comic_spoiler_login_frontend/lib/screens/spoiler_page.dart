import 'dart:io';
import 'package:comic_spoiler_login_frontend/screens/login_page.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/auth_service.dart';

class SpoilerPage extends StatefulWidget {
  final AuthService authService;

  const SpoilerPage({super.key, required this.authService});

  @override
  State<SpoilerPage> createState() => _SpoilerPageState();
}

class _SpoilerPageState extends State<SpoilerPage> {
  File? _imageFile;
  String? _result;
  bool _isLoading = false;

  Future<void> pickImage() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);

    if (pickedFile != null) {
      setState(() {
        _imageFile = File(pickedFile.path);
        _result = null;
      });
    }
  }

  Future<void> analyzeImage() async {
    if (_imageFile == null) {
      setState(() {
        _result = 'No image selected!';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _result = null;
    });

    final data = await widget.authService.analyzeImage(_imageFile!);

    setState(() {
      if (data.containsKey('error')) {
        _result = 'Error: ${data['error']}';
      } else {
        _result =
            '''
✅ Extracted Text: ${data['extracted_text']}
🗒️ Caption: ${data['caption']}
🎭 Genre: ${data['genre']}
👤 Character Count: ${data['character_count']}
🚨 Spoiler: ${data['spoiler_result']}
''';
      }
      _isLoading = false;
    });
  }

  Future<void> testConnection() async {
    final status = await widget.authService.testConnection();
    setState(() {
      _result = status;
    });
  }

  Future<void> logout() async {
    bool success = await widget.authService.logout();
    if (success) {
      if (mounted) {
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(
            builder: (_) => LoginPage(),
          ), // <-- make sure to import it!
          (route) => false,
        );
      }
    } else {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Logout failed')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Comic Spoiler Detector')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton(onPressed: logout, child: const Text('Logout')),
              const SizedBox(height: 20),

              ElevatedButton(
                onPressed: pickImage,
                child: const Text('Pick Image'),
              ),
              const SizedBox(height: 20),

              ElevatedButton(
                onPressed: testConnection,
                child: const Text('Test Connection'),
              ),
              const SizedBox(height: 20),

              ElevatedButton(
                onPressed: analyzeImage,
                child: const Text('Analyze'),
              ),
              const SizedBox(height: 20),

              if (_imageFile != null)
                Image.file(_imageFile!, width: 200, height: 200),
              const SizedBox(height: 20),

              if (_isLoading)
                const CircularProgressIndicator()
              else if (_result != null)
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(_result!, style: const TextStyle(fontSize: 16)),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

// import 'package:flutter/material.dart';
// import 'dart:io';
// import 'package:image_picker/image_picker.dart';
// import '../services/spoiler_service.dart';

// class SpoilerPage extends StatefulWidget {
//   @override
//   _SpoilerPageState createState() => _SpoilerPageState();
// }

// class _SpoilerPageState extends State<SpoilerPage> {
//   final SpoilerService _spoilerService = SpoilerService();
//   File? _image;
//   String _result = '';

//   Future<void> _pickAndAnalyzeImage() async {
//     final picker = ImagePicker();
//     final picked = await picker.pickImage(source: ImageSource.gallery);

//     if (picked != null) {
//       final file = File(picked.path);

//       setState(() {
//         _image = file; // ✅ store picked image for preview
//         _result = 'Analyzing...'; // show temporary status
//       });

//       final result = await _spoilerService.analyzeImage(file);
//       setState(() {
//         _result = _formatResult(result);
//       });
//     }
//   }

//   String _formatResult(Map<String, dynamic> result) {
//     return '''
// Extracted Text: ${result['extracted_text']}
// Caption: ${result['caption']}
// Genre: ${result['genre']}
// Character Count: ${result['character_count']}
// Spoiler Result: ${result['spoiler_result']}
// ''';
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(title: Text('Comic Spoiler Detector')),
//       body: SingleChildScrollView(
//         padding: const EdgeInsets.all(20),
//         child: Column(
//           children: [
//             ElevatedButton(
//               onPressed: _pickAndAnalyzeImage,
//               child: Text('Pick Image & Analyze'),
//             ),
//             SizedBox(height: 20),

//             if (_image != null) ...[
//               Text('Selected Image:'),
//               SizedBox(height: 10),
//               Image.file(_image!, width: 300, fit: BoxFit.cover),
//               SizedBox(height: 20),
//             ],

//             Text('Result:', style: TextStyle(fontWeight: FontWeight.bold)),
//             SizedBox(height: 10),
//             Text(_result),
//           ],
//         ),
//       ),
//     );
//   }
// }
