FROM python:3.9-slim

# تثبيت متطلبات النظام (FFmpeg, ImageMagick)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libespeak-ng1 \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# إصلاح سياسات ImageMagick
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml

WORKDIR /app

# نسخ الملفات
COPY requirements.txt .
RUN pip install --no-cache-dir flask gunicorn
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# تشغيل الخادم
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--timeout", "300", "app:app"]