# 🇩🇪 Deutsch Meister PRO — Telegram Bot

Nemis tilini o'rgatuvchi Telegram bot. Railway orqali deploy qilingan.

## Xususiyatlar
- 🤖 AI Mentor (Vorstellen + Aktiv Sprechen)
- 📖 Lug'at (A1-C1, admin tomonidan to'ldiriladi)
- 🌐 Tarjimon (UZB ↔ DEU)
- 📚 Sayfa va Kitob Materiallar
- 📖 Kunlik so'z
- 📊 Progress (JPG grafik)
- 📝 Test (darajaga qarab)
- 🔐 Admin Panel (foydalanuvchilar, xabar yuborish, statistika)

## Railway Environment Variables
```
BOT_TOKEN=your_bot_token
GROQ_API_KEY=your_groq_key
ADMIN_IDS=your_telegram_id
MINI_APP_URL=https://your-mini-app.railway.app
DATABASE_PATH=deutsch_meister.db
```

## Loyiha tuzilmasi
- `main.py` — asosiy bot kodi (2283 qator)
- `database.py` — SQLite ma'lumotlar bazasi (18 jadval)
- `config.py` — konfiguratsiya va mavzular
- `seed_aktiv_data.py` — 2500 ta so'z va 100 ta hikoya bazaga yuklash
