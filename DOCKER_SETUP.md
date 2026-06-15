# Docker Setup Guide (دليل إعداد Docker)

## 🐳 تشغيل المشروع باستخدام Docker

### المتطلبات
- Docker ([تحميل](https://www.docker.com/products/docker-desktop))
- Docker Compose (يأتي مع Docker Desktop)

---

## ⚡ البدء السريع

### 1. بناء الصورة
```bash
docker build -t hr-system:latest .
```

### 2. تشغيل الحاوية
```bash
docker run -p 5000:5000 \
  -v $(pwd)/core:/app/core \
  -v $(pwd)/app/static/uploads:/app/app/static/uploads \
  hr-system:latest
```

### 3. الوصول للتطبيق
```
http://localhost:5000
```

---

## 🚀 استخدام Docker Compose (الموصى به)

### البدء
```bash
docker-compose up -d
```

### إيقاف الخدمة
```bash
docker-compose down
```

### عرض السجلات
```bash
docker-compose logs -f hr-system
```

### إعادة بناء الصورة
```bash
docker-compose up -d --build
```

---

## 📁 هيكل الملفات

```
.
├── Dockerfile              # تعريف الصورة
├── docker-compose.yml      # تكوين Docker Compose
├── .dockerignore          # الملفات المستثناة
├── .env.example           # مثال على متغيرات البيئة
├── requirements.txt       # التبعيات
└── run.py                # نقطة الدخول
```

---

## 🔧 الإعدادات المتقدمة

### تغيير المنفذ
```bash
docker run -p 8080:5000 hr-system:latest
```

### تعيين متغيرات البيئة
```bash
docker run -p 5000:5000 \
  -e FLASK_ENV=development \
  -e FLASK_DEBUG=1 \
  hr-system:latest
```

### استخدام ملف .env
```bash
docker run -p 5000:5000 \
  --env-file .env \
  hr-system:latest
```

---

## 📊 مراقبة الحاوية

### عرض الحاويات الجارية
```bash
docker ps
```

### عرض السجلات
```bash
docker logs <container-id>
```

### الدخول للحاوية
```bash
docker exec -it <container-id> /bin/bash
```

### إحصائيات الاستخدام
```bash
docker stats
```

---

## 🌐 النشر السحابي

### على Heroku
```bash
heroku login
heroku create your-app-name
heroku container:push web
heroku container:release web
```

### على AWS (ECS)
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag hr-system:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/hr-system:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/hr-system:latest
```

### على Google Cloud Run
```bash
gcloud auth configure-docker
docker tag hr-system:latest gcr.io/your-project/hr-system:latest
docker push gcr.io/your-project/hr-system:latest
gcloud run deploy hr-system --image gcr.io/your-project/hr-system:latest --platform managed
```

### على DigitalOcean
```bash
doctl auth init
doctl registry login
docker tag hr-system:latest registry.digitalocean.com/your-registry/hr-system:latest
docker push registry.digitalocean.com/your-registry/hr-system:latest
```

---

## 🔒 الأمان

### تغيير المفتاح السري
```bash
# في .env
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
```

### تفعيل HTTPS
```bash
# استخدم reverse proxy مثل Nginx
# أو استخدم خدمة مثل Let's Encrypt
```

---

## 🐛 استكشاف الأخطاء

### المشكلة: الحاوية تتوقف فوراً
```bash
docker logs <container-id>
```

### المشكلة: لا يمكن الوصول للتطبيق
```bash
# تحقق من المنفذ
docker port <container-id>

# تحقق من الاتصال
curl http://localhost:5000
```

### المشكلة: قاعدة البيانات مفقودة
```bash
# تأكد من تعيين المجلد
docker run -v $(pwd)/core:/app/core ...
```

---

## 📝 ملاحظات مهمة

1. **قاعدة البيانات**: يتم حفظها في `core/hr.db` على الجهاز المضيف
2. **الملفات المرفوعة**: يتم حفظها في `app/static/uploads`
3. **السجلات**: يتم حفظها في `logs/`
4. **الأداء**: استخدم `docker-compose` للإنتاج

---

**آخر تحديث**: 2026-06-15