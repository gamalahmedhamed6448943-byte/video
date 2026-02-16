from flask import Flask, request, send_file, render_template_string
from video_engine import process_video
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Video Generator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 20px; text-align: center; }
        input { width: 80%; padding: 10px; margin: 10px 0; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>تحويل المقال إلى فيديو</h1>
    <form action="/generate" method="post">
        <input type="text" name="url" placeholder="ضع رابط المقال هنا..." required>
        <br>
        <button type="submit">إنشاء الفيديو</button>
    </form>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    url = request.form.get('url')
    video_path, error = process_video(url)
    
    if video_path:
        try:
            return send_file(video_path, as_attachment=True, download_name="final_video.mp4")
        finally:
            # تم الإبقاء على الحذف معلقاً كما في طلبك
            pass
    else:
        return f"Error: {error}", 500

if __name__ == '__main__':
    # Gunicorn سيقوم بتجاوز هذا السطر، لكنه مفيد للتجربة المحلية
    app.run(host='0.0.0.0', port=5000)