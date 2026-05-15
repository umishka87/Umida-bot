"""
Telegram-бот для канала @AiContentCreatorUZ
- 2 поста в день
- Серия Midjourney на 9 дней (14-22 мая 2026)
- Включает урок про написание промптов и бан-лист
- После — обычные темы БЕЗ промптов и БЕЗ агентов
"""

import os
import random
import logging
from datetime import datetime, timezone, timedelta, date
import requests
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from anthropic import Anthropic

# ============================================
# НАСТРОЙКИ
# ============================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_USERNAME = "@AiContentCreatorUZ"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
INSTAGRAM_USERNAME = "@umishka_abdukarimova"

PUBLISH_ON_STARTUP = True

SERIES_START_DATE = date(2026, 5, 14)
SERIES_DAYS = 9

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# СЕРИЯ MIDJOURNEY (9 дней × 2 поста = 18 постов)
# ============================================

MIDJOURNEY_SERIES = {
    # День 1 (14 мая) — Знакомство
    (0, "morning"): "mj_intro",
    (0, "evening"): "mj_business",
    # День 2 (15 мая) — Реклама и итог
    (1, "morning"): "mj_advertising",
    (1, "evening"): "mj_summary",
    # День 3 (16 мая) — НОВЫЕ УРОКИ про промпты
    (2, "morning"): "mj_prompts_howto",
    (2, "evening"): "mj_banned_words",
    # День 4 (17 мая) — Версии
    (3, "morning"): "mj_versions",
    (3, "evening"): "mj_niji",
    # День 5 (18 мая) — Режимы
    (4, "morning"): "mj_stealth",
    (4, "evening"): "mj_modes",
    # День 6 (19 мая) — Платформа и параметры
    (5, "morning"): "mj_discord_web",
    (5, "evening"): "mj_parameters",
    # День 7 (20 мая) — Стили и Instagram
    (6, "morning"): "mj_styles",
    (6, "evening"): "mj_instagram",
    # День 8 (21 мая) — Ошибки
    (7, "morning"): "mj_mistakes",
    (7, "evening"): "mj_tips",
    # День 9 (22 мая) — Итоги
    (8, "morning"): "mj_advanced",
    (8, "evening"): "mj_week_summary",
}

# ============================================
# РАСПИСАНИЕ ПОСЛЕ СЕРИИ (БЕЗ агентов, БЕЗ промптов!)
# ============================================

POST_SCHEDULE = {
    (0, "morning"): "news",
    (0, "evening"): "reflection",
    (1, "morning"): "insight",
    (1, "evening"): "tool_review",
    (2, "morning"): "news",
    (2, "evening"): "trend",
    (3, "morning"): "insight",
    (3, "evening"): "tool_review",
    (4, "morning"): "news",
    (4, "evening"): "story",
    (5, "morning"): "case",
    (5, "evening"): "weekend_reflection",
    (6, "morning"): "easy_post",
    (6, "evening"): "tool_review",
}

IMAGE_THEMES = {
    "mj_intro": ["digital art", "creative AI", "abstract art"],
    "mj_business": ["business creative", "branding studio", "marketing"],
    "mj_advertising": ["luxury advertising", "product photography", "cinematic"],
    "mj_summary": ["creative workspace", "design studio", "art"],
    "mj_prompts_howto": ["writing creative", "notebook ideas", "creative process"],
    "mj_banned_words": ["warning sign", "stop sign", "caution"],
    "mj_versions": ["technology evolution", "digital innovation", "modern art"],
    "mj_niji": ["anime style", "illustration", "creative drawing"],
    "mj_stealth": ["privacy business", "security", "professional"],
    "mj_modes": ["speed motion", "creative process", "studio"],
    "mj_discord_web": ["modern interface", "digital workspace", "technology"],
    "mj_parameters": ["control panel", "creative tools", "design"],
    "mj_styles": ["art styles", "creative variety", "artistic"],
    "mj_instagram": ["social media", "instagram content", "creative photography"],
    "mj_mistakes": ["learning", "improvement", "creative process"],
    "mj_tips": ["lightbulb idea", "success tips", "motivation"],
    "mj_advanced": ["mastery", "professional art", "expertise"],
    "mj_week_summary": ["completion", "achievement", "creative success"],
    "news": ["technology news", "innovation", "digital future"],
    "insight": ["business insight", "marketing", "industry"],
    "reflection": ["thinking", "workspace", "minimalism"],
    "trend": ["modern technology", "digital trend", "future"],
    "story": ["narrative", "business journey", "creative"],
    "case": ["success", "business growth", "achievement"],
    "weekend_reflection": ["coffee", "lifestyle", "calm"],
    "easy_post": ["sunset", "calm", "minimalism"],
    "tool_review": ["software", "tech tools", "modern"],
}

# ============================================
# CTA
# ============================================

CTA_LIST = [
    "\n\n📸 Mening barcha ishlarim Instagram'da: {ig}",
    "\n\n💼 Brendingiz uchun AI-video kerakmi? Umidaga yozing: {ig}",
    "\n\n🔥 100 obunachiga yetganda — birinchi sirni ochaman. Do'stlaringizga ulashing!",
    "\n\n💾 Postni saqlab qo'ying — kerak bo'ladi.",
    "\n\n🚀 AI bilan ijod qilayotganlar uchun kanal. Obuna bo'ling.",
    "\n\n🎬 Umida brendlar uchun AI-reklamalar yaratadi. Instagram: {ig}",
]


def get_cta() -> str:
    cta = random.choice(CTA_LIST)
    return cta.format(ig=INSTAGRAM_USERNAME)


# ============================================
# ГЛОБАЛЬНОЕ ПРАВИЛО для всех постов
# ============================================

GLOBAL_RULE = """

QAT'IY QOIDALAR (HAR DOIM AMAL QILING):
1. HECH QACHON tayyor prompt yozmang — bu Umidaning shaxsiy mulki.
2. HECH QACHON "Prompt:" deb boshlanuvchi matn yozmang.
3. HECH QACHON ingliz tilida tirnoq ichida AI uchun ko'rsatma bermang.
4. Misol kerak bo'lsa — UMUMIY tushuncha bering, aniq prompt EMAS.
5. Markdown formatlash YO'Q (yulduzcha, pastki chiziq).
6. Kod blok belgilarini ishlatmang.
7. Faqat O'zbek tili LATIN harflarda.
8. AI-agentlar haqida HECH NARSA yozmang.
"""


# ============================================
# ПРОМПТЫ ДЛЯ ПОСТОВ
# ============================================

POST_PROMPTS = {
    # ===== СЕРИЯ MIDJOURNEY (9 дней, 18 постов) =====
    
    "mj_intro": """Midjourney haqida birinchi post. Mavzu: TANISHUV + NARXLAR + RO'YXATDAN O'TISH.

OHANG: do'stona, hayratlanarli.

ANIQ MA'LUMOTLAR (2026):
- Midjourney — eng yaxshi AI-rasm vositasi, kinematografik sifat
- Bepul tarif YO'Q (2024 yildan)
- Tariflar:
  Basic $10/oy ($8 yillik) — 200 rasm
  Standard $30/oy ($24) — eng mashhur, cheksiz Relax
  Pro $60/oy ($48) — Stealth Mode
  Mega $120/oy ($96) — professional
- Yillik to'lov — 20% chegirma
- Sayt: midjourney.com

STRUKTURA:
- Sarlavha (emoji)
- Midjourney nima (2-3 gap)
- Narxlar
- Qaysi tarif tavsiya (Standard $30)
- Qanday boshlash (sayt orqali)
- 2-3 hashtag

Max 1000 belgi.""",

    "mj_business": """Midjourney 2-post. Mavzu: vs NANO BANANA + BIZNES UCHUN + QACHON KERAK EMAS.

OHANG: tajribali maslahatchi, halol.

MAZMUN:
1. Farq: Midjourney — kinematografik, premium, badiiy. Nano Banana — tezroq, texnik.
2. Biznes uchun: reklama, brand-kontent, mahsulot katalogi, Instagram.
3. KERAK EMAS: aniq odam yuzi, rasm ichida matn, juda ko'p rasm tez, byudjet yo'q.

STRUKTURA:
- Sarlavha
- Farqi nimada
- Biznes foydasi
- Qachon kerak emas (halol)
- 2-3 hashtag

Max 1000 belgi.""",

    "mj_advertising": """Midjourney 3-post. Mavzu: REKLAMA vs ART + MAHSULOT HIKOYASI.

MAZMUN:
1. Midjourney yaxshi qiladi: ART (kinematografik), REKLAMA (premium).
2. Boshqalar yaxshiroq: tez mahsulot — Nano Banana, portret — Flux.
3. Hikoya (ismsiz): brend ko'p sarflagan, foyda kichik. Midjourney bilan vizual qayta qilingan, sotuv 2 baravar oshgan.

STRUKTURA:
- Sarlavha
- Midjourney nimani yaxshi qiladi
- Boshqalar nimani yaxshi qiladi
- Hikoya
- Xulosa
- 2-3 hashtag

Max 1000 belgi.""",

    "mj_summary": """Midjourney 4-post. Mavzu: KIMGA KERAK — XULOSA.

KERAK: premium vizual, SMM, dizayner, reklama agentligi, Instagram kontent.
KERAK EMAS: birinchi sinov, byudjet yo'q, faqat kundalik rasmlar, texnik aniqlik.
TAVSIYA: Standard $30 boshlash. Pro $60 jiddiy ish. Yillik -20%.

STRUKTURA:
- Sarlavha
- Kimga kerak
- Kimga kerak emas
- Tavsiya
- Yakun
- 2-3 hashtag

Max 1000 belgi.""",

    # ===== УРОК 5: КАК ПИСАТЬ ПРОМПТЫ =====
    "mj_prompts_howto": """Midjourney 5-post. MUHIM DARS: Promptni qanday yozish kerak.

MAQSAD: O'qituvchanlik, lekin AYNAN tayyor prompt yozmasdan!
DIQQAT: misol berishingiz mumkin, lekin u TO'LIQ tayyor prompt bo'lmasin — UMUMIY tushuncha.

MAZMUN:

1. Prompt nima:
- Sizning fikringizni AI'ga tushuntirish usuli
- To'g'ri yozsangiz — chiroyli natija

2. Prompt tuzilmasi (4 element):
- Asosiy mavzu (nima rasm)
- Uslub (cinematic, illustration, photo, art)
- Atmosfera (yorug'lik, kayfiyat)
- Texnik detallar (4K, sharp)

3. Asosiy qoidalar:
- Inglizcha yozing — natija yaxshiroq
- Iboralarni vergul bilan ajrating
- 2-3 tasvirlovchi so'z yetadi
- Ortiqcha so'zlar chalkashtiradi

4. Maslahat: ChatGPT yoki Claude prompt yozishga yordam beradi
- Ammo natijani tekshiring — taqiqlangan so'zlar bo'lishi mumkin
- Ertaga: TAQIQLANGAN so'zlar ro'yxati

STRUKTURA:
- Sarlavha (emoji)
- Prompt nima
- 4 elementi
- Asosiy qoidalar
- Anons: ertaga taqiqlangan so'zlar
- 2-3 hashtag

MUHIM: aniq tayyor promptni misol qilib yozmang!
Max 1000 belgi.""",

    # ===== УРОК 6: БАН-ЛИСТ =====
    "mj_banned_words": """Midjourney 6-post. JUDA MUHIM: TAQIQLANGAN SO'ZLAR — akkaunt blokirovkadan saqlash.

OHANG: jiddiy, ogohlantirish.

MAZMUN:

KIRISH: Midjourney qattiq filtr ishlatadi. Taqiqlangan so'z = prompt rad etiladi. Qayta urinish = akkaunt bloklanadi.

TAQIQLANGAN KATEGORIYALAR:

1. ZO'RAVONLIK / QON
Misol so'zlar (inglizcha): blood, gore, dead, wound, severed, kill, weapon
Almashtiring: "dark fantasy", "dramatic atmosphere"

2. KATTALAR KONTENTI
Misol: nude, naked, sexy, erotic, porn
DIQQAT: filtr hatto "voluptuous", "provocative", "scantily clad" so'zlarini ham tutadi
Almashtiring: "elegant portrait", "graceful pose"

3. KIYIM (ochiq)
Misol: lingerie, see-through, revealing
Almashtiring: "fashionable outfit", "stylish dress"

4. NARKOTIKLAR
Misol: cocaine, heroin, meth, weed
Almashtiring: "psychedelic", "neon glow"

5. NAFRAT VA KAMSITISH
Irqchilik, kamsituvchi so'zlar — taqiqlangan

6. REAL ODAMLAR
Mashhur siyosatchilar — ehtiyot bo'ling, ayniqsa salbiy kontekstda

MUHIM ESLATMA:
- Filtr SINONIMLARNI ham tutadi
- Boshqacha yozish ishlamaydi
- Filtrni aldashga urinmang — akkaunt bloklanadi
- "Bobongizga ko'rsata olmaydigan" mavzulardan saqlaning
- Midjourney PG-13 standartda ishlaydi

XULOSA: ijodiy alternatif so'zlar toping. Akkauntingizni asrang.

STRUKTURA:
- Sarlavha (ogohlantirish emoji)
- Nima uchun muhim
- 6 ta kategoriya (har biriga 1-2 misol va alternatif)
- Eslatma
- Xulosa
- 2-3 hashtag

Max 1300 belgi (caption uchun ko'proq).""",

    "mj_versions": """Midjourney 7-post. Mavzu: VERSIYALAR — V6, V7.

MAZMUN:
- V1 dan V7 gacha rivojlangan
- V6.1 — 2025 oxir, barqaror
- V7 — 2026 yangi, eng kuchli
- V7 yaxshiliklari: aniqroq yuz, qo'l, matn, yaxshi kompozitsiya
- Eski versiyalar mavjud
- Tavsiya: V7 yangi loyiha, V6 barqaror natija

STRUKTURA:
- Sarlavha
- Versiyalar tarixi
- V6 vs V7
- Qaysisini tanlash
- 2-3 hashtag

Max 900 belgi.""",

    "mj_niji": """Midjourney 8-post. Mavzu: NIJI MODE — anime va illyustratsiya.

MAZMUN:
- Niji — maxsus rejim
- Anime, manga, illyustratsiya
- Yaponcha estetika
- Bolalar kitoblari, mascot uchun ideal
- Niji vs oddiy: yumshoq, yorqin ranglar
- Qachon: anime, illyustratsiya zarurat

STRUKTURA:
- Sarlavha
- Niji nima
- Qachon ishlatish
- Misol vaziyatlar
- 2-3 hashtag

Max 900 belgi.""",

    "mj_stealth": """Midjourney 9-post. Mavzu: STEALTH MODE — biznes uchun maxfiylik.

MAZMUN:
- Pro va Mega tariflarda
- Rasmlaringiz boshqalar ko'ra olmaydi
- NDA loyihalar, mahsulot launch, patent himoyasi
- Oddiy tariflarda — ish ommaviy
- Agentliklar va studiyalar uchun

STRUKTURA:
- Sarlavha
- Stealth Mode nima
- Kimga kerak
- Qaysi tarifda
- 2-3 hashtag

Max 900 belgi.""",

    "mj_modes": """Midjourney 10-post. Mavzu: RELAX vs FAST.

MAZMUN:
- Fast: 30-60 soniya, GPU soati hisobiga
- Relax: 1-10 daqiqa, cheksiz (Standard'dan)
- Fast — shoshilinch, Relax — eksperiment
- Basic — faqat Fast (200 rasm)
- Strategiya: muhim — Fast, qidiruv — Relax

STRUKTURA:
- Sarlavha
- Ikki rejim farqi
- Qachon Fast / Relax
- 2-3 hashtag

Max 900 belgi.""",

    "mj_discord_web": """Midjourney 11-post. Mavzu: Discord vs veb-sayt.

MAZMUN:
- Avval faqat Discord edi
- 2024-2025 veb-sayt to'liq ishga tushdi
- Sayt: qulay, galereya, tahrirlash
- Discord: tezroq, jamoa
- Yangilar — saytdan, tajribali — ikkala joyda
- Hisob bir xil

STRUKTURA:
- Sarlavha
- Discord tarixi
- Veb-sayt afzalliklari
- Qaysi tanlash
- 2-3 hashtag

Max 900 belgi.""",

    "mj_parameters": """Midjourney 12-post. Mavzu: PARAMETRLAR — umumiy tushuncha.

DIQQAT: aniq parametr kodlarini yozmang!

MAZMUN:
- Parametrlar — rasm boshqaruvi
- Asosiy: o'lcham, uslub kuchi, variatsiyalar, versiyalar
- Yangilar — parametrsiz boshlasin
- Tajriba bilan o'rganib boriladi

STRUKTURA:
- Sarlavha
- Parametrlar nima
- Asosiy turlari
- Maslahat
- 2-3 hashtag

Max 900 belgi.""",

    "mj_styles": """Midjourney 13-post. Mavzu: USLUBLAR.

USLUBLAR:
- Fotorealistik
- Cinematic
- Illustration
- Anime/manga
- Vintage/retro
- Minimalistik
- Abstract
- 3D render
- Watercolor

QACHON QAYSI:
- Reklama — fotorealistik, cinematic
- Bolalar — illustration, anime
- Brend — minimalist

STRUKTURA:
- Sarlavha
- Uslublar
- Qachon qaysi
- 2-3 hashtag

Max 900 belgi.""",

    "mj_instagram": """Midjourney 14-post. Mavzu: INSTAGRAM kontenti.

MAZMUN:
- Stories vizuallari
- Reels fonlari
- Carousel postlar
- Highlight cover
- Reklama kreativlari

Formatlar: 9:16 (Stories), 1:1 (post), 4:5 (post)
Strategiya: bir uslub — vizual brending
Maslahat: 5-10 rasm tayyor, haftaga yetadi

STRUKTURA:
- Sarlavha
- Qayerda ishlatish
- Formatlar
- Strategiya
- 2-3 hashtag

Max 900 belgi.""",

    "mj_mistakes": """Midjourney 15-post. Mavzu: TOP-5 XATO.

5 XATO:
1. Birinchi natijaga ishonish — 5-10 marta sinab ko'ring
2. Juda ko'p detal — oddiy boshlang
3. Sifatga e'tibor yo'q — Standard minimum
4. Bitta uslub — eksperiment qiling
5. Galereya o'rganmaslik — boshqalar ishidan ilhom

STRUKTURA:
- Sarlavha
- 5 xato
- Asosiy maslahat
- 2-3 hashtag

Max 900 belgi.""",

    "mj_tips": """Midjourney 16-post. Mavzu: PROFESSIONAL maslahatlar.

5 MASLAHAT:
1. Bir loyiha uchun bir uslubni saqlang
2. Ranglar palitrasini oldindan tanlang
3. Referans rasmlar yig'ing
4. Yaxshi natijani galereyaga saqlang
5. Discord'da boshqa ijodkorlar ishini kuzating

STRUKTURA:
- Sarlavha
- 5 maslahat
- Yakun
- 2-3 hashtag

Max 900 belgi.""",

    "mj_advanced": """Midjourney 17-post. Mavzu: KEYINGI BOSQICH — qachon Midjourney'dan o'tib boshqaga.

MAZMUN:
- Midjourney — boshlang'ich va o'rta daraja uchun ideal
- Professional ish uchun qo'shimcha vositalar:
  • Photoshop — yakuniy ishlov
  • Topaz — sifat oshirish
  • Krea — real-time generatsiya
  • Flux — alternatif AI
- Midjourney + Photoshop = professional natija
- Faqat AI'ga tayanmang — qo'l ishlovi muhim

STRUKTURA:
- Sarlavha
- Midjourney imkoniyatlari chegarasi
- Qo'shimcha vositalar
- Maslahat
- 2-3 hashtag

Max 900 belgi.""",

    "mj_week_summary": """Midjourney 18-post. HAFTA YAKUNI.

MAZMUN:
9 kunlik darslar haqida qisqacha:
- Tanishuv, narxlar
- Biznes uchun
- Promptlar va taqiqlangan so'zlar
- Versiyalar, Niji, Stealth
- Rejimlar, parametrlar
- Uslublar, Instagram
- Xatolar va maslahatlar

KEYINGI HAFTA: AI-soha yangiliklari va trendlari.

RAHMAT: obunachilarga minnatdorchilik. 100 obunachiga yetishimizga yordam bering.

STRUKTURA:
- Sarlavha (yakun emoji)
- Nima o'rgandik
- Keyingisi nima
- Rahmat va so'rov
- 2-3 hashtag

Max 1000 belgi.""",

    # ===== ОБЫЧНЫЕ ТЕМЫ =====

    "news": """AI-soha yangiligi posti.

Mavzu: umumiy AI yangiligi yoki trendi (Midjourney emas, agent emas).

OHANG: insayder.

STRUKTURA:
- Sarlavha (emoji)
- Yangilik (2-3 gap)
- Nima uchun qiziq
- 2-3 hashtag

Max 600 belgi.""",

    "insight": """Insayt posti.

OHANG: kuzatuv.

Mavzu: AI yoki marketing (agentlar emas).

STRUKTURA:
- Sarlavha
- Kuzatuv (3-4 gap)
- Xulosa
- 2-3 hashtag

Max 600 belgi.""",

    "reflection": """Mulohaza posti.

OHANG: shaxsiy, do'stona.

Mavzu: AI ijodi, kelajak.

STRUKTURA:
- Sarlavha
- Mulohaza (3-4 gap)
- Savol
- 2-3 hashtag

Max 600 belgi.""",

    "trend": """Trend haqida.

Mavzu: AI yoki marketing trendi (agent emas).

STRUKTURA:
- Sarlavha
- Trend
- Nima uchun muhim
- 2-3 hashtag

Max 600 belgi.""",

    "story": """Hikoya posti (ismsiz, umumiy).

STRUKTURA:
- Sarlavha
- Vaziyat
- Voqea
- Natija
- 2-3 hashtag

Max 800 belgi.""",

    "case": """Keys-post (ismsiz).

STRUKTURA:
- Sarlavha
- Muammo
- Yechim
- Natija
- 2-3 hashtag

Max 800 belgi.""",

    "weekend_reflection": """Dam olish kuni mulohazasi.

OHANG: yengil.

STRUKTURA:
- Sarlavha
- Mulohaza (3-4 gap)
- 2-3 hashtag

Max 500 belgi.""",

    "easy_post": """Yengil yakshanba posti.

OHANG: iliq.

STRUKTURA:
- Sarlavha
- Fikr (2-3 gap)
- 2 hashtag

Max 400 belgi.""",

    "tool_review": """AI-vosita sharhi (Midjourney EMAS, agent EMAS).

Tavsiya: Suno AI, Flux, ChatGPT, Runway, Pika, ElevenLabs, Adobe Firefly.

STRUKTURA:
- Sarlavha
- Vosita nomi
- Afzalliklari
- Narxi (umumiy)
- 2-3 hashtag

Max 700 belgi.""",
}


# ============================================
# ГЕНЕРАЦИЯ
# ============================================

def generate_post(post_type: str) -> str:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    base_prompt = POST_PROMPTS.get(post_type, POST_PROMPTS["news"])
    full_prompt = base_prompt + GLOBAL_RULE
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": full_prompt}]
    )
    
    text = message.content[0].text
    cta = get_cta()
    return text + cta


# ============================================
# КАРТИНКА
# ============================================

def get_image_url(post_type: str) -> str:
    themes = IMAGE_THEMES.get(post_type, ["technology"])
    query = random.choice(themes)
    
    url = "https://api.unsplash.com/photos/random"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {"query": query, "orientation": "landscape"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["urls"]["regular"]
    except Exception as e:
        logger.error(f"Ошибка получения картинки: {e}")
        return None


# ============================================
# ВЫБОР ТЕМЫ
# ============================================

def get_post_type(time_of_day: str) -> str:
    tashkent_tz = timezone(timedelta(hours=5))
    today = datetime.now(tashkent_tz).date()
    
    days_from_start = (today - SERIES_START_DATE).days
    
    if 0 <= days_from_start < SERIES_DAYS:
        post_type = MIDJOURNEY_SERIES.get((days_from_start, time_of_day))
        if post_type:
            logger.info(f"🎯 Серия Midjourney: день {days_from_start+1}/{SERIES_DAYS}, {time_of_day}")
            return post_type
    
    weekday = datetime.now(tashkent_tz).weekday()
    return POST_SCHEDULE.get((weekday, time_of_day), "news")


# ============================================
# ПУБЛИКАЦИЯ
# ============================================

async def publish_post(time_of_day: str = "morning"):
    try:
        post_type = get_post_type(time_of_day)
        logger.info(f"📝 Тип поста: {post_type} ({time_of_day})")
        
        text = generate_post(post_type)
        logger.info(f"✅ Текст сгенерирован, {len(text)} символов")
        
        image_url = get_image_url(post_type)
        
        bot = Bot(token=BOT_TOKEN)
        
        if len(text) > 1024:
            text = text[:1020] + "..."
        
        if image_url:
            await bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=image_url,
                caption=text
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=text
            )
        
        logger.info("✅ Пост опубликован!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации: {e}")


async def publish_morning():
    await publish_post("morning")


async def publish_evening():
    await publish_post("evening")


async def keep_alive_ping():
    tashkent_tz = timezone(timedelta(hours=5))
    current_time = datetime.now(tashkent_tz).strftime("%H:%M:%S")
    logger.info(f"💚 Keep-alive — Ташкент: {current_time}")


# ============================================
# ЗАПУСК
# ============================================

async def main():
    if PUBLISH_ON_STARTUP:
        logger.info("🧪 Тестовая публикация при запуске...")
        tashkent_tz = timezone(timedelta(hours=5))
        current_hour = datetime.now(tashkent_tz).hour
        time_of_day = "morning" if current_hour < 14 else "evening"
        await publish_post(time_of_day)
    
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    scheduler.add_job(
        publish_morning,
        CronTrigger(hour=8, minute=0),
        id="morning_post",
        replace_existing=True
    )
    
    scheduler.add_job(
        publish_evening,
        CronTrigger(hour=19, minute=0),
        id="evening_post",
        replace_existing=True
    )
    
    scheduler.add_job(
        keep_alive_ping,
        IntervalTrigger(minutes=10),
        id="keep_alive",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Бот запущен. Серия Midjourney 9 дней (14-22 мая).")
    
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
