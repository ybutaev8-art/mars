# 🤖 MARS ELEKTRON TEXNIKA - TELEGRAM BOTI
## Yangi kompyuterda ishga tushirish bo'yicha qo'llanma

Ushbu arxivda botning barcha kodlari, so'nggi ma'lumotlar bazasi (`data/` ichidagi barcha Excel, sessiya va tiketlar) to'liq jamlangan.

---

### 🚀 1-qadam. Python kutubxonalarini o'rnatish
Kompyuterda terminal (PowerShell yoki CMD) ochib, bot papkasiga kiring va quyidagi buyruqni bering:
```bash
pip install -r requirements.txt
```

---

### ▶️ 2-qadam. Botni ishga tushirish
Botni fonda (ekranda qora oyna chiqmasdan) ishga tushirish uchun:
* PowerShell orqali:
```powershell
.\start_bot.ps1
```
yoki sichqoncha bilan `run_background.bat` faylini 2 marta bosing.

---

### 🔍 3-qadam. Bot holatini tekshirish
Bot ishlab turganini bilish uchun:
```powershell
.\check_status.ps1
```

---

### 🛑 4-qadam. Botni to'xtatish yoki qayta yuklash
* To'xtatish uchun:
```powershell
.\stop_bot.ps1
```
* O'zgarishlar kiritilgandan so'ng qayta yuklash uchun:
```powershell
.\restart_bot.ps1
```

---

### 📂 Muhim fayllar tavsifi:
* `bot.py` - Asosiy Telegram bot kodi va barcha xabarlar marshrutizatsiyasi.
* `ticket_service.py` - Texnik va mijoz o'rtasidagi yagona jonli kartochka va muloqot xizmati.
* `telegraph_service.py` - Telegram Instant View (tarix va rasmlar) xizmati.
* `excel_service.py` - Oylik to'lovlar jadvali (4900+ STIR) bilan ishlash tizimi.
* `image_analyzer.py` - Apparat ekranidagi nosozlik rasmlarini tahlil qilish (OCR).
* `receipt_service.py` - To'lov cheklari (Click, Payme, bank) kvitansiyalarini tekshirish.
* `config.py` - Bot sozlamalari, tokenlar va adminlar ID lari.
* `data/abonent_jadvali.xlsx` - Mijozlar ro'yxati va qarzdorlik holati.
