FROM python:3.9-slim

# 1. تثبيت متطلبات النظام الأساسية و ImageMagick
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libespeak-ng1 \
    ghostscript \
    findutils \
    && rm -rf /var/lib/apt/lists/*

# 2. إصلاح سياسات ImageMagick (بحث ذكي عن الملف)
# هذا الأمر يبحث عن policy.xml في أي مجلد داخل /etc ويقوم بتعديله
RUN find /etc -name "policy.xml" -exec sed -i 's/none/read,write/g' {} +

WORKDIR /app

# 3. نسخ المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir flask gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# 4. نسخ باقي الملفات
COPY . .

# 5. تشغيل الخادم
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--timeout", "300", "app:app"]