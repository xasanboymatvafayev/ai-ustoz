# 🚀 AI Ustoz — Deploy Qo'llanmasi
## Railway (Backend) + Vercel (Frontend)

---

## 📁 Papka strukturasi

```
deploy/
├── backend/               ← Railway ga bu papkani yuklang
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── requirements.txt
│   ├── Procfile
│   ├── railway.json
│   ├── nixpacks.toml
│   ├── .env
│   ├── models/
│   │   └── models.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── groups.py
│   │   ├── assignments.py
│   │   └── websocket.py
│   └── services/
│       ├── ai_checker.py
│       └── jwt_service.py
│
└── frontend/              ← Vercel ga bu papkani yuklang
    ├── index.html
    ├── dashboard.html
    ├── student.html
    ├── config.js          ← ← ← MUHIM: Railway URL shu yerda
    └── vercel.json
```

---

## 🚂 RAILWAY — BACKEND DEPLOY

### 1-qadam: GitHub repo yaratish

```bash
# backend papkasiga kiring
cd backend

# Git init
git init
git add .
git commit -m "AI Ustoz backend"

# GitHub da yangi repo yarating: ai-ustoz-backend
git remote add origin https://github.com/SIZNING_USERNAME/ai-ustoz-backend.git
git push -u origin main
```

### 2-qadam: Railway.app da deploy

1. **https://railway.app** ga kiring
2. **"New Project"** bosing
3. **"Deploy from GitHub repo"** tanlang
4. `ai-ustoz-backend` repo ni tanlang
5. Railway avtomatik deploy qiladi ✅

### 3-qadam: Environment Variables qo'shish

Railway dashboard → sizning proyekt → **Variables** tab:

| Variable | Qiymat |
|----------|--------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:OiXhlXFVpVCJpkeUzmArneQXdCTeFNkG@mainline.proxy.rlwy.net:34199/railway` |
| `SECRET_KEY` | `95951223sabriya-95951223sabriya` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` |

### 4-qadam: Domain olish

Railway → sizning servis → **Settings** → **Networking** → **Generate Domain**

Siz olgan URL shunday ko'rinadi:
```
https://ai-ustoz-backend-production.up.railway.app
```

✅ **Shu URL ni yozib oling — keyingi qadamda kerak bo'ladi!**

---

## ▲ VERCEL — FRONTEND DEPLOY

### 1-qadam: config.js ni yangilash

`frontend/config.js` faylini oching va Railway URL ingizni kiriting:

```javascript
// Shu qatorni o'zgartiring:
const API_BASE = 'https://AI-USTOZ-SIZNING-URL.up.railway.app';
```

Masalan:
```javascript
const API_BASE = 'https://ai-ustoz-backend-production.up.railway.app';
```

### 2-qadam: GitHub repo yaratish

```bash
# frontend papkasiga kiring
cd frontend

git init
git add .
git commit -m "AI Ustoz frontend"

# GitHub da yangi repo: ai-ustoz-frontend
git remote add origin https://github.com/SIZNING_USERNAME/ai-ustoz-frontend.git
git push -u origin main
```

### 3-qadam: Vercel.com da deploy

1. **https://vercel.com** ga kiring (GitHub bilan login)
2. **"New Project"** bosing
3. `ai-ustoz-frontend` repo ni tanlang
4. Settings:
   - **Framework Preset**: `Other`
   - **Root Directory**: `/` (bo'sh qoldiring)
   - **Build Command**: bo'sh (build kerak emas)
   - **Output Directory**: bo'sh
5. **Deploy** bosing ✅

### 4-qadam: Vercel domain

Vercel avtomatik beradi:
```
https://ai-ustoz-frontend.vercel.app
```

---

## 🔗 CORS SOZLASH (Railway backend da)

Railway backendga qaytib, `main.py` dagi CORS qismini o'zgartiring:

```python
allow_origins=[
    "https://ai-ustoz-frontend.vercel.app",  # ← Vercel URL ingiz
    "https://*.vercel.app",
]
```

Keyin commit va push:
```bash
git add . && git commit -m "fix cors" && git push
```
Railway avtomatik qayta deploy qiladi.

---

## ✅ TEKSHIRISH

1. Railway URL + `/api/health` → `{"status":"ok"}` ko'rsatishi kerak
2. Vercel URL → Login sahifasi ochilishi kerak
3. O'quvchi ro'yxatdan o'tishi → email kod kelishi kerak
4. O'qituvchi 🔑 bosib, `fizika1` kiritsa → dashboard ochilishi kerak

---

## 🆘 XATOLAR VA YECHIMLAR

### "CORS error" ko'rsatsa
- Railway `main.py` da Vercel URL ni `allow_origins` ga qo'shing

### "Database connection error"
- Railway Variables da `DATABASE_URL` to'g'ri ekanligini tekshiring
- URL `postgresql+asyncpg://` bilan boshlanishi kerak (postgres:// emas!)

### "Module not found"
- `requirements.txt` da barcha paketlar borligini tekshiring
- Railway → Deployments → oxirgi deploy loglarini ko'ring

### EmailJS ishlamasa
- Browser Console (F12) da kod ko'rinadi
- EmailJS dashboard da template to'g'ri ekanligini tekshiring

---

## 🔑 MUHIM MA'LUMOTLAR

| Narsa | Qiymat |
|-------|--------|
| O'qituvchi maxsus kaliti | `fizika1` |
| EmailJS Service | `service_pa8gy9p` |
| EmailJS Template | `template_oqf4m5n` |
| DB Host | `mainline.proxy.rlwy.net:34199` |
