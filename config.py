"""
Mars Elektron Texnika MCHJ - Texnik Xizmat Telegram Boti Konfiguratsiyasi
"""
import os

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8927157387:AAE-wxQsDf5WPhgVu6uNQLP45J-iI7hKVqA")

# Ma'lumotlar bazasi va Excel fayllari yo'li
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCEL_PATH = os.path.join(DATA_DIR, "abonent_jadvali.xlsx")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

# Suhbat sessiyasi muddati (soatda) - foydalanuvchi talabiga ko'ra 8 soat
SESSION_TTL_HOURS = 8

# Tashkilot ma'lumotlari
COMPANY_NAME = "MARS ELEKTRON TEXNIKA MCHJ"
COMPANY_PHONE = "+998 94 299 77 99"
TECHNICIAN_TELEGRAM_ID = 6436610869
TECHNICIAN_USERNAME = "@Yashnarbek_butaev"
ADMIN_TELEGRAM_IDS = [6436610869, 360332364]
ADMIN_USERNAMES = ["@Yashnarbek_butaev", "@MARSSMARTSALELLC"]

# Texniklar kanali va unga bog'langan Muhokama (Fikr bildirish) guruhi
TECHNICIAN_CHANNEL_ID = -1004327901839  # @mars_tex_xizmat
TECHNICIAN_CHANNEL_USERNAME = "@mars_tex_xizmat"
DISCUSSION_GROUP_ID = -1004332222960   # Kanalga bog'langan sharhlar (muhokama) guruhi

# Video va qo'llanmalar (Rekvizitlar, darsliklar va xatolarni tuzatish) kanali
MATERIALS_CHANNEL_ID = -1001641871516  # @POS_Terminal_UzSmart_Bank
MATERIALS_CHANNEL_USERNAME = "@POS_Terminal_UzSmart_Bank"
MATERIALS_CHANNEL_URL = "https://t.me/POS_Terminal_UzSmart_Bank"

# Excel hisob-kitob jadvallarini avtomatik monitoring va forward qilish
EXCEL_SOURCE_GROUP_ID = -1001795471853    # Абонент тулови🏦💸💰
EXCEL_TARGET_CHANNEL_ID = -1004405333505  # Oylik abanit (https://t.me/+1KOqeABGySo1M2Iy)

# Oylik abonent to'lovi rekvizitlari (Telegram kanaldagi rasmiy ko'rinish)
REKVIZIT_OYLIK = """CLIK to'lov tizimi orqali oylik abanit to'lovini to'lash tartibi

Clik dasturiga kirasiz > tolovlar bolimida > Rekvizit bo'yicha to'lov > Rasmdagi kurinishda tuldiriladi

Abanet tulov uchun shot

«MARS ELEKTRON TEXNIKA» МЧЖ
Манзил: г. Шахрисабз улица Шерозий 1
Абонент Х/Р: `20 20 8000 800 208 044 003`
Банк: «Ипак Йули» АИТ банки Шахрисабз филиали МФО: `01048`  ИНН: `302568138`
Тел: +998 94 299 77 99,  моб:+99891-945-32-89
Тулов максади: Абонент тулов 100 000 сум бир ойлик"""

# Oylik to'lov video qo'llanmasi matni
VIDEO_OYLIK_CAPTION = """Oylik abanit tulovni Clickdan utkazish varianti
👇👇👇👇👇👇
Tulov Maqsadiga uzingizni tashkelotingiz malomotlarini kiritishni unitmang!"""

# Yillik fiskal modul to'lovi rekvizitlari (Telegram kanaldagi rasmiy ko'rinish)
REKVIZIT_YILLIK = """Yillik Fiscal modul tulovi uchun shot

«Yangi Texnologiyalar» DUK
Х/Р: `2021 0000 1004 3120 0010`
МФО: `01018`
ИНН: `201 589 463`
Tulov kodi: `00668`
Tulov maqsadi: INN [Sizning INN] fiskal modulning yillik tulovi
Tulov summasi: 440 000 so'm
Tel: +998 71 202 32 32

ℹ️ Tulov qilingandan sung 2 soatdan 24 soat ichida ishlab ketadi Fiscal modul"""

# Video qo'llanmalar (Havolalar yoki fayllar)
VIDEO_OYLIK_URL = "https://t.me/POS_Terminal_UzSmart_Bank/148"
VIDEO_YILLIK_URL = "https://t.me/POS_Terminal_UzSmart_Bank/145"
VIDEO_CLOCK_URL = "https://t.me/POS_Terminal_UzSmart_Bank/141"
VIDEO_IKPU_URL = "https://t.me/POS_Terminal_UzSmart_Bank/126"

# Sun'iy intellekt (Google Gemini AI) integratsiyasi
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6JD8ZebojWkiSMDLE9qyxmjftSna03tFS744MoifNIj5g")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

