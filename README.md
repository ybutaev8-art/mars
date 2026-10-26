# 🤖 "MARS ELEKTRON TEXNIKA" MCHJ - Texnik Xizmat Telegram Boti

Online nazorat-kassa apparatlari (NKA / virtual kassa) bo'yicha texnik xizmat ko'rsatuvchi, mijozlarga muammolar bo'yicha avtomatik javob beruvchi, hisob-kitob jadvallaridan oylik qarzdorlikni va fiskal modul yillik to'lovlarini tekshiruvchi professional Telegram bot.

---

## 📌 Asosiy Imkoniyatlar

1. **Telegram Guruhda Ishlash:**
   - Bot guruhda bir vaqtning o'zida bir nechta mijoz bilan alohida ishlay oladi.
   - Har bir mijozga aynan uning yozgan xabariga **reply (belgilab)** qilib javob beradi.
   - Har bir mijoz bilan bo'layotgan suhbat holatini (sessiyasini) **8 soat** davomida saqlab turadi.

2. **Muloqot va Intellektual Tahlil:**
   - **Salomlashish:** *"Salom! Men MARS ELEKTRON TEXNIKA MCHJ ning texnik hizmat kursatuvchi telegram botiman sizga qanday yordam kerak"*
   - **Aparat nosozligi ("Aparatim ishlamayapti", "Ko'rib beringlar"):**
     Bot darhol: *"Tashkilotingizning INN yoki JSHSHIR raqamini yuboring. Ma'lumot uchun: STIR deb yozilgan bo'limda ko'rsatilgan."*
   - **Oylik to'lovni TEKSHIRISH vs TO'LASH farqlanishi:**
     - Tekshiruv so'rovlarida to'lov darsligi bilan adashtirmaydi, INN so'raydi.
     - To'lash so'rovlarida oylik abonent to'lash video darsligi va rekvizitlarini taqdim etadi.
   - **Yillik to'lovni TEKSHIRISH vs TO'LASH farqlanishi:**
     - Tekshiruv so'rovlarida FM raqamini so'raydi (pastki qismdagi FM bo'limi).
     - To'lash so'rovlarida yillik fiskal modul to'lov video darsligi va rekvizitlarini taqdim etadi.

3. **Excel Oylik Abonent Jadvalidan Tekshirish:**
   - INN yoki JSHSHIR yuborilganda jadvaldan qidiradi:
     - **Qarzdorlik bo'lsa:** Qancha qarz borligi va to'lov rekvizitlarini ko'rsatadi.
     - **Qarzdorlik bo'lmasa:** *"Aparatingizni internetga ulanganligini va soati tugri ekanligini tekshiring aparatni internetga ulab uchirib yoqish (perezagruska) qilish tafsiya etiladi. Alohida yillik feskal modul tulovingizni tekshirib berishimni istasangiz aparatingizni feskal modul raqamini yuboring."*

4. **Fiskal Modul va @ofd943bot Integratsiyasi:**
   - FM raqami yuborilganda yillik fiskal modul xizmat muddati tekshiriladi va OFD ma'lumotlari bilan javob qaytariladi.

5. **Texnik Admin bilan Bog'lash:**
   - Agar mijozning oylikdan ham, yillikdan ham qarzi bo'lmasa va mijoz *"Aparatim ishlamayabdiku / unda nimaga ishlamayapti?"* deb yozsa, bot mijozni mas'ul admin / texnik xodim bilan bog'laydi va adminlarga xabar yuboradi.

6. **Excel Jadvalini Jonli Yangilash:**
   - Admin botga yoki guruhga yangi `.xlsx` yoki `.csv` hisob-kitob jadvalini tashlasa, bot uni avtomatik qabul qilib bazani yangilaydi.

---

## 🚀 Ishga Tushirish

Loyihani ishga tushirish uchun papkadagi `run_bot.bat` faylini ikki marta bosing yoki terminalda:

```powershell
& "C:\Users\Yashnar\AppData\Local\Programs\Python\python311\python.exe" bot.py
```

---

## ⚙️ Sozlamalar (`config.py`)

- `BOT_TOKEN`: Telegram bot tokeni (`8927157387:AAE-wxQsDf5WPhgVu6uNQLP45J-iI7hKVqA`)
- `SESSION_TTL_HOURS = 8`: Mijoz sessiyasining amal qilish muddati (soatda)
- `REKVIZIT_OYLIK`: Oylik to'lov bank rekvizitlari va Payme/Click ma'lumotlari
- `REKVIZIT_YILLIK`: Yillik Fiskal Modul to'lovi rekvizitlari
- `VIDEO_OYLIK_URL`: Oylik to'lov video darsligi havolasi
- `VIDEO_YILLIK_URL`: Yillik to'lov video darsligi havolasi
- `ADMIN_USERNAMES`: Guruhda chaqiriladigan admin username'lari
- `ADMIN_TELEGRAM_IDS`: To'g'ridan-to'g'ri chaqiruv xabari boradigan adminlar telegram ID'si

---

## 👥 Telegram Guruhda Sozlash Qoidalari

1. Botni Telegram guruhga qo'shing (`@txkmrobot`).
2. Guruhda botga **Administrator** huquqini bering.
3. BotFather ga kirib:
   - `/mybots` -> botingizni tanlang -> `Bot Settings` -> `Group Privacy` -> **Turn off** (Disabled) qiling.
   - Bu orqali bot guruhdagi mijozlarning barcha savollarini bemalol ko'rib javob bera oladi.
