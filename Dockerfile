FROM python:3.9-slim

# 1. تثبيت متطلبات النظام
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libespeak-ng1 \
    ghostscript \
    findutils \
    && rm -rf /var/lib/apt/lists/*

# 2. إصلاح سياسات ImageMagick
RUN find /etc -name "policy.xml" -exec sed -i 's/none/read,write/g' {} +

WORKDIR /app

# 3. تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir flask gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# 4. إعداد NLTK
RUN mkdir -p /app/nltk_data && chmod 777 /app/nltk_data
ENV NLTK_DATA=/app/nltk_data

# 5. نسخ الملفات ومنح الصلاحيات
COPY . .
RUN chmod -R 777 /app

# كشف المنفذ 8000 لـ Koyeb
EXPOSE 8000

# 6. التشغيل (تعديل المنفذ من 7860 إلى 8000 ليتوافق مع Koyeb)
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "300", "app:app"]