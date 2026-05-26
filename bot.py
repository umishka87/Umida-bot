"""
Telegram-бот для канала @AiContentCreatorUZ
ВЕРСИЯ 3.0 — финальная

Изменения от 2.0:
- 30 готовых постов серии AI-видеогенерация (с проверенной информацией)
- 30 готовых дневных постов про AI и будущее
- Только РАБОЧИЕ узбекские хештеги (проверены)
- Убрана серия CRM (отменена)
- Убрана Sora (модель закрыта 26 апреля 2026)
- Убрана Seedance (по запросу)
- HeyGen перенесён на следующий месяц (отдельная серия)
- 4 поста в день: 7:00 / 13:00 / 17:00 / 19:00 Ташкент
- В коде UTC: 2:00 / 8:00 / 12:00 / 14:00
- Опросы Пн/Ср/Пт в 20:00 (15:00 UTC)
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

# ============================================
# НАСТРОЙКИ
# ============================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_USERNAME = "@AiContentCreatorUZ"
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

INSTAGRAM_URL = "https://www.instagram.com/umishka_abdukarimova?utm_source=qr"

PUBLISH_ON_STARTUP = False

# Серия AI-видеогенерации стартует 23 мая 2026
SERIES_VIDEO_START = date(2026, 5, 23)
SERIES_VIDEO_TOTAL_POSTS = 30  # 30 постов = 15 дней по 2 поста

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================
# ХЕШТЕГИ — ТОЛЬКО РАБОЧИЕ УЗБЕКСКИЕ
# Проверено: миллионы постов на каждом
# ============================================

# Главные локальные (миллионы постов)
HASHTAGS_MAIN = [
    "#uzbekistan", "#tashkent", "#toshkent", "#uzb",
    "#uzbek", "#uzbekiston", "#tashkentcity"
]

# Регионы
HASHTAGS_REGIONS = [
    "#andijon", "#namangan", "#samarkand", "#buxoro", "#fargona"
]

# Telegram
HASHTAGS_TELEGRAM = [
    "#telegram_yulduzlari", "#zortv", "#yulduzlari", "#telegram"
]

# Узбекский язык/культура
HASHTAGS_CULTURE = [
    "#uzbekcha", "#uzbegim", "#uzbeks", "#uzbekistan_inst"
]


def get_hashtags(count: int = 10) -> str:
    """Возвращает 10 рабочих узбекских хештегов."""
    selected = []
    # 4 главных (всегда)
    selected += random.sample(HASHTAGS_MAIN, 4)
    # 2 региональных
    selected += random.sample(HASHTAGS_REGIONS, 2)
    # 2 telegram
    selected += random.sample(HASHTAGS_TELEGRAM, 2)
    # 2 культурных
    selected += random.sample(HASHTAGS_CULTURE, 2)
    
    return " ".join(selected[:count])


# ============================================
# CTA — с Instagram ссылкой
# ============================================

CTA_LIST = [
    # === С Instagram ===
    f"\n\n📸 Mening ishlarim Instagram'da: {INSTAGRAM_URL}",
    f"\n\n💼 Brendingiz uchun AI-video kerakmi? Yozing: {INSTAGRAM_URL}",
    f"\n\n🎬 AI-reklama namunalari Instagram'da: {INSTAGRAM_URL}",
    f"\n\n👀 Ko'proq AI-ishlar Instagram'da: {INSTAGRAM_URL}",
    f"\n\n💼 AI-yechim kerakmi biznesingizga? Yozing: {INSTAGRAM_URL}",
    f"\n\n🌟 Davom etishni xohlasangiz — Instagram'ga obuna bo'ling: {INSTAGRAM_URL}",
    
    # === Без ссылки — рост канала ===
    "\n\n🔥 Foydali bo'lsa — yurakcha bosing ❤️",
    "\n\n🤝 AI'ga qiziquvchi do'stingiz bormi? Unga shu kanalni yuboring.",
    "\n\n💬 Savollar bormi? Sharhlarda yozing — javob beraman.",
    "\n\n💾 Postni saqlab qo'ying — kerak bo'ladi.",
    "\n\n📤 Postni ish chatingizga tashlang — hamkasblarga ham foydali.",
    "\n\n🎯 Bugun nima yangi narsa bilib oldingiz? Sharhlarda ulashing!",
    "\n\n🌟 Kanalga obuna bo'ling — har kuni AI haqida yangi narsa.",
    "\n\n❤️ Yoqdimi? Yurakcha qo'ying — bu menga muhim.",
]


def get_cta() -> str:
    return random.choice(CTA_LIST)


# ============================================
# УТРЕННИЕ ПРИВЕТСТВИЯ (7:00) — БЕЗ дня недели
# ============================================

MORNING_GREETINGS = [
    """🌅 Hayrli tong, hurmatli do'stlar! ☕

Bugungi maqsadingiz nima? Bitta narsani yozing — kichik bo'lsa ham.

Sharhlarda yozing, bir-birimizga turtki beraylik 🙌

Kuningiz yaxshi o'tsin! 🌟""",

    """🌅 Hayrli tong! ☀️

Hurmatli do'stlar, bugun nimani ichdingiz — choymi yoki kofemi?

Sharhlarda javob bering, qiziq 😊

Kuningiz mazmunli o'tsin! ✨""",

    """🌅 Hayrli tong! 🌸

Hurmatli do'stlar, bugun qanday his qilyapsiz — 1 dan 10 gacha?

Halol javob bering, mana shu yerda 😄

Kuningiz yorug' o'tsin! 🌟""",

    """🌅 Hayrli tong! 💪

Hurmatli do'stlar, kechagi kun yaxshi o'tdimi?
Bugun bir kichik narsa qilamiz — birga harakat qilaylik.

Sharhlarda yozing — sizning kuningiz qanday boshlanyapti? 🌅

Yaxshi kun bo'lsin! ✨""",

    """🌅 Hayrli tong! 🌴

Hurmatli do'stlar, ertalab nima yedingiz?
Tushlik uchun rejangiz bormi?

Sharhlarda yozing — birga ulashaylik 🍞

Kuningiz quvonchli o'tsin! 🌟""",

    """🌅 Hayrli tong! 🌞

Hurmatli do'stlar, AI bilan biror narsa qilmoqchimisiz bugun?

Yoki shunchaki qiziq mavzumi? Sharhlarda yozing 💬

Kuningiz yaxshi o'tsin! 🌟""",

    """🌅 Hayrli tong, hurmatli do'stlar! ☕

Yangi kun — yangi imkoniyatlar.
Bugun bitta yangi narsa o'rganaylik.

Sharhlarda yozing — siz nimani o'rganmoqchisiz? 🎯

Kuningiz baroakali bo'lsin! ✨""",
]


def get_morning_greeting() -> str:
    return random.choice(MORNING_GREETINGS)


# ============================================
# ОПРОСЫ
# ============================================

POLLS = [
    {
        "question": "AI'dan kunlik foydalanasizmi? 🤖",
        "options": ["Ha, har kuni", "Ba'zan", "Hech qachon"]
    },
    {
        "question": "Yoshingiz nechada? 👋",
        "options": ["20 gacha", "20-30", "30-40", "40+"]
    },
    {
        "question": "AI'ning qaysi yo'nalishi sizga qiziq? 🎯",
        "options": ["Rasmlar", "Video", "Matn", "Biznes uchun"]
    },
    {
        "question": "AI odamlarni ishdan qoldiradi deb o'ylaysizmi? 🤔",
        "options": ["Ha, ishonchli", "Yo'q", "Bilmadim"]
    },
    {
        "question": "AI bilan ishlashni o'rganmoqchimisiz? 📚",
        "options": ["Ha, juda", "Balki", "Yo'q"]
    },
    {
        "question": "Qaysi AI-video modelda ishlagansiz? 🎬",
        "options": ["Kling", "Runway", "Veo", "Boshqa / Hali yo'q"]
    },
    {
        "question": "Sizga qaysi mavzu qiziq? 💡",
        "options": [
            "Video yaratish",
            "Rasm generatsiyasi",
            "AI bilan pul ishlash",
            "Instagram va AI"
        ]
    },
]


# ============================================
# СЕРИЯ AI-ВИДЕОГЕНЕРАЦИИ — 30 ГОТОВЫХ ПОСТОВ
# Все факты проверены на май 2026
# ============================================

VIDEO_SERIES_POSTS = [
    # ========== ПОСТ 1 — Обзор моделей ==========
    """🎬 AI-video modellari — qaysi biri sizga kerak?

Hurmatli do'stlar, AI-video bozori 2026 yilda juda tez o'zgardi. Bugun haqiqiy taqqoslashni beraman.

📊 Asosiy modellar:

KLING 3.0 — №1 reytingda. Realistik insonlar, murakkab harakatlar, 4K sifat.

VEO 3.1 (Google) — eng yaxshi sifat va ovoz sinxronlashuvi.

RUNWAY Gen-4.5 — professional vositalar, kamera nazorati.

PIKA 2.5 — tezkor va qulay. Pikaffects effektlari.

LUMA Dream Machine — kinematografik manzaralar uchun.

HAILUO — arzon va sifatli. Inson yuzlari yaxshi.

HIGGSFIELD — cinematic kamera harakatlari uchun.

⚠️ Sora (OpenAI) 26-aprelda yopildi.

🎯 Qanday tanlash:
• Reklama → Kling yoki Veo
• Sosial tarmoqlar → Pika yoki Kling
• Professional → Runway

Ertaga — Kling 3.0 haqida batafsil.

Qaysi modellarda ishlagansiz?""",

    # ========== ПОСТ 2 — Kling 3.0 ==========
    """🎯 Kling 3.0 — AI-video lideri 2026

Hurmatli do'stlar, bugun Kling haqida — hozirgi eng kuchli model.

Nima ajralib turadi:

✨ Realistik inson harakatlari
Yuzlar, qo'llar, tana harakatlari haqiqiy. "Plastik" effekt yo'q.

✨ Multi-shot
Bitta videoda 6 ta kadrgacha. Bir prompt — butun hikoya.

✨ Native 4K sifat
Kino sifati to'g'ridan-to'g'ri.

✨ Ovoz va lablar sinxronlashuvi
5 tilda gapiradi.

✨ Motion Control
Boshqa videodan harakatni ko'chirish — noyob xususiyat.

Kim uchun yaxshi:
• Reklamalar (kiyim, kosmetika)
• Kinematografik sahnalar
• E-commerce video
• TikTok, Reels uchun
• Realistik insonlar bilan sahnalar

Kamchiliklari:
• Abstrakt effektlar uchun emas
• Aniq prompt kerak

60 mln ijodkor 600 mln video yaratgan.

Ertaga — Runway Gen-4.5.""",

    # ========== ПОСТ 3 — Runway Gen-4.5 ==========
    """🎬 Runway Gen-4.5 — professional standart

Hurmatli do'stlar, bugun Runway — agentliklar va prodyuserlar tanlovi.

Nima qila oladi:

✨ Eng yaxshi kamera nazorati
Dolly, crane, tracking shotlarni aniq belgilash mumkin.

✨ Reference image
Bir rasm beraman — Runway uning uslubida video yaratadi.

✨ Character consistency
Bir personaj turli sahnalarda bir xil ko'rinishda qoladi.

✨ In-platform editor
Hammasi bir joyda — generatsiya, montaj, effektlar.

✨ Gen-4 Turbo
Tezkor rejim — bir necha soniyada natija.

Kim uchun yaxshi:
• Reklama agentliklari
• Film studiyalari
• Brend videolari
• Yuqori darajadagi reklamalar

Kamchiliklari:
• Native ovoz hozircha yo'q
• 16 sekunddan uzoq video qila olmaydi
• Qimmatroq

Mening tavsiyam:
Mijoz uchun — Runway. Tezkor kontent — boshqa modellar.

Ertaga — Veo 3.1.""",

    # ========== ПОСТ 4 — Veo 3.1 ==========
    """🎬 Veo 3.1 — Google'dan eng yangi

Hurmatli do'stlar, Veo 3.1 — 2026-yanvarda chiqdi va bozorni o'zgartirdi.

Nima ajralib turadi:

✨ Native 4K vertikal video
TikTok, Reels, YouTube Shorts uchun tayyor format.

✨ Sinxron ovoz va lablar
Video bilan birga ovoz ham generatsiya qiladi.

✨ Realizm cho'qqisi
Yorug'lik, soyalar, kamera chuqurligi — fotorealistik.

✨ Scene extension
Bir generatsiyani uzaytirish mumkin — 60+ sekundlik sahnalar.

✨ Character consistency
Bir personaj turli sahnalarda bir xil.

Kim uchun yaxshi:
• Hero shotlar (asosiy reklama kadri)
• Vertikal sosial kontent
• Realistik mahsulot videolari
• Ovozli reklamalar
• Brend hikoyalari

Kamchiliklari:
• Asosan AQSh foydalanuvchilariga ochiq
• 10-20 sek optimal uzunlik
• Uzbek tilida lab sinxronlashuvi yo'q

Veo + Kling — eng kuchli juftlik.

Ertaga — Pika 2.5.""",

    # ========== ПОСТ 5 — Pika 2.5 ==========
    """⚡ Pika 2.5 — tezlik va effektlar

Hurmatli do'stlar, Pika — sosial tarmoq ijodkorlari uchun zo'r tanlov.

Asosiy fishkalar:

✨ Pikaffects
Noyob vizual effektlar — boshqa modellarda yo'q. Tez xayoliy video uchun.

✨ Pikaswaps
Videoda obyektlarni almashtirish — odam yuzini, mahsulotni va boshqalar.

✨ Pikadditions
Videoga yangi obyekt qo'shish — sehrli effekt.

✨ Pikaformance
Gapiruvchi rasm — fotoga ovoz qo'shadi.

✨ Tezlik
Bir necha soniyada natija — Runway va Kling'dan tezroq.

Kim uchun yaxshi:
• TikTok va Instagram kontent
• Viral videolar
• Eksperimentlar
• Tezkor reklamalar
• Yangi boshlovchilar

Kamchiliklari:
• Sifat Kling va Veo'dan past
• Murakkab sahnalar qiyin
• Realistik insonlar — yaxshi emas

Mening tavsiyam:
Sosial tarmoqlar uchun tezkor kontent — Pika. Sifatli reklama — Kling yoki Veo.

Ertaga — Luma Dream Machine.""",

    # ========== ПОСТ 6 — Luma Dream Machine ==========
    """🌌 Luma Dream Machine — kinematografik manzaralar

Hurmatli do'stlar, Luma — manzaralar va atmosfera ustasi.

Nima yaxshi qiladi:

✨ Tabiat va manzaralar
Tog'lar, dengiz, o'rmon, shahar — Luma bularni hammadan yaxshi qiladi.

✨ Atmosfera va kayfiyat
Yorug'lik, tuman, soyalar — kinematografik darajada.

✨ Ray3 versiyasi
4K HDR sifat, fizika simulyatsiyasi yaxshi.

✨ Tezkor 5 sek kliplar
Image-to-video — bir rasmdan video. Tez va sifatli.

✨ Dream Machine rejimi
Erkin kreativ generatsiya — abstrakt va xayoliy ishlar uchun.

Kim uchun yaxshi:
• Sayohat brendlari
• Restoran va kafelar (atmosfera)
• Mehmonxonalar
• Tabiatga oid kontent
• Brending va mood videolari

Kamchiliklari:
• Insonlar — Kling'dan past
• Ovoz yo'q
• Qisqa kliplar

Mening tavsiyam:
Manzaralar va atmosfera kerak bo'lsa — Luma. Insonlar bilan — Kling.

Ertaga — Hailuo MiniMax.""",

    # ========== ПОСТ 7 — Hailuo / MiniMax ==========
    """💎 Hailuo (MiniMax) — arzon va sifatli

Hurmatli do'stlar, Hailuo — Xitoydan tezkor o'sayotgan model.

Nima yaxshi:

✨ Inson yuzlari
Yuz ifodalari, ko'z harakatlari — juda yaxshi.

✨ Tabiiy harakat
Sekin va realistik — "plastik" effekti yo'q.

✨ Arzon
Bozordagi eng arzonlardan biri. Boshlang'ich foydalanuvchilar uchun zo'r.

✨ Image-to-video kuchli
Bir rasm — qiziqarli video.

✨ Tezkor generatsiya
Bir-ikki daqiqada video tayyor.

Kim uchun yaxshi:
• Yangi boshlovchilar
• Kichik byudjet
• Portretli videolar
• E-commerce mahsulotlar
• Reklama eksperimentlari

Kamchiliklari:
• Murakkab sahnalar qiyin
• Kamera nazorati cheklangan
• Ovoz yo'q

Mening tavsiyam:
AI-videoga endi kirmoqchimisiz — Hailuo. Tajriba ortgach — Kling yoki Runway.

Ertaga — Higgsfield haqida.""",

    # ========== ПОСТ 8 — Higgsfield ==========
    """🎥 Higgsfield — cinematic kamera ustasi

Hurmatli do'stlar, Higgsfield — kinematografik shotlar uchun maxsus model.

Nima ajralib turadi:

✨ Kamera harakati
Bullet time, orbital shots, crash zoom — sinemada ko'rganlaringiz.

✨ Cinematic effects
Kinodan oyirib bo'lmaydigan darajada.

✨ Character animation
Personajlar bilan dinamik sahnalar.

✨ Reklama uchun zo'r
Mahsulot atrofida kamera aylanishi, dramatik kirish kadrlari.

✨ Omni Reference
Bitta referensdan bir nechta sahna — brend uchun mukammal.

Kim uchun yaxshi:
• Reklama videolari
• Brend hikoyalari
• Musiqa klipi uchun shotlar
• Mahsulot reklamalari
• Kichik kreativ proyektlar

Kamchiliklari:
• Yuzlar ba'zan buziladi
• 5-10 sekundlik videolar
• Murakkab promptlar qiyin

Mening tavsiyam:
Higgsfield + Kling — kuchli kombinatsiya. Higgsfield kamera harakati uchun, Kling — asosiy sahna.

Ertaga — qanday modelni tanlash haqida.""",

    # ========== ПОСТ 9 — Как выбрать модель ==========
    """🎯 AI-video modelni qanday tanlash?

Hurmatli do'stlar, ko'p model bor — qaysi birini olish kerak? Bugun savol-javob.

Savol 1: Sizning maqsadingiz nima?

Reklama (mijoz uchun): Runway yoki Kling
Sosial tarmoqlar (TikTok, Reels): Pika yoki Kling
Manzaralar va atmosfera: Luma
Realistik insonlar: Kling yoki Veo
Cinematic effects: Higgsfield
Tejamkor variant: Hailuo

Savol 2: Tajribangiz qancha?

Yangi boshlovchi: Hailuo yoki Pika (tezkor, oddiy)
O'rta darajadagi: Kling (eng baland)
Professional: Runway, Veo (ko'p sozlamalar)

Savol 3: Byudjet qancha?

Bepul boshlash: Kling (66 kredit/kun)
Kichik byudjet: Hailuo, Pika
O'rta byudjet: Kling Standard, Veo
Yuqori byudjet: Runway Pro, Kling Premier

Maslahat:
1 ta modelda tajriba ortmasdan boshqasiga o'tmang. Avval bittasini chuqur o'rganing.

Ko'pchilik 2-3 modelni birga ishlatadi:
• Kling — asosiy sahnalar
• Runway — kamera nazorati kerak bo'lganda
• Pika — tezkor sosial kontent

Ertaga — AI-video uchun promptlar.""",

    # ========== ПОСТ 10 — Промпты основы ==========
    """✍️ AI-video promptlari — asoslari

Hurmatli do'stlar, prompt — bu AI'ga matnli ko'rsatma. Endi qiziqarli qism.

Yaxshi promptning 3 ta qismi:

1. SAHNA — nima sodir bo'lyapti
Kim, qayerda, nima qilyapti.
Masalan: "Yosh ayol kofehonada noutbukda ishlayapti"

2. KAMERA — qanday suratga olinadi
Yaqin kadr, uzoq kadr, kamera harakati.
Masalan: "Close-up shot, slow zoom in"

3. ATMOSFERA — kayfiyat va yorug'lik
Yorug'lik turi, vaqt, rang palitrasi.
Masalan: "Warm golden hour lighting, cozy atmosphere"

❌ Yomon prompt:
"Ayol kofe ichyapti"

✅ Yaxshi prompt:
"Close-up shot of young woman holding ceramic cup, steam rising, warm cafe atmosphere, golden afternoon light, slow cinematic zoom"

Asosiy maslahatlar:

• Inglizcha yozing — natija yaxshi
• Aniq bo'ling, ammo ortiqcha emas
• Texnik so'zlar kuchli ishlaydi (cinematic, shallow depth)
• 30-80 so'z optimal uzunlik

Aniq promptlar bermayman — bu mening shaxsiy mulkim. Lekin printsiplar shu.

Ertaga — Kling uchun promptlar.""",

    # ========== ПОСТ 11 — Промпты Kling ==========
    """🎯 Kling uchun promptlar — uslubi

Hurmatli do'stlar, har bir modelning o'z uslubi bor. Bugun — Kling.

Kling nimani yaxshi tushunadi:

✅ Tabiiy harakatlar
"Walking", "running", "dancing" — Kling buni zo'r qiladi.

✅ Inson hissiyotlari
"Smiling", "looking surprised", "crying" — yuz ifodalari aniq.

✅ O'rta tezlikdagi sahnalar
Tez harakatlar (jangchi, sport) — qiyin. Sekin (gulning ochilishi) — zo'r.

✅ Realistik portretlar
Bir kishi yaqin kadr — Kling'da eng yaxshi.

Kling nimani yoqtirmaydi:

❌ Juda murakkab sahnalar
6 dan ortiq odam, ko'p obyekt — buziladi.

❌ Tez kamera harakati
Crash zoom — yaxshi emas. Sekin dolly — zo'r.

❌ Abstrakt effektlar
Sehrli, syurrealistik — Pika yaxshi qiladi.

Maslahatlar Kling uchun:

• Promptingiz qisqa bo'lsin (30-50 so'z)
• 1-2 ta asosiy harakatga e'tibor
• Yorug'lik tafsilotlarini bering
• "Realistic", "natural" so'zlarini ishlating

Ertaga — Runway uchun promptlar.""",

    # ========== ПОСТ 12 — Промпты Runway ==========
    """🎬 Runway uchun promptlar — professional

Hurmatli do'stlar, Runway texnik tilni yaxshi tushunadi. Kino-tili bilan ishlaydi.

Runway uchun foydali so'zlar:

KAMERA:
• Dolly in/out — kamera ichkari/tashqari
• Tracking shot — obyekt ortidan
• Crane shot — yuqoridan pastga
• Whip pan — tez aylanish
• Static shot — qotirilgan

OBYEKTIV:
• Wide angle — keng burchak
• Telephoto — uzoqdan yaqinlashtirish
• Macro — juda yaqin

CHUQURLIK:
• Shallow depth of field — orqa fon xira
• Deep focus — hamma fokusda
• Bokeh — fonida nurli aylanalar

YORUG'LIK:
• Rim lighting — orqa nuri
• Soft box — yumshoq nur
• Hard light — qattiq soya
• Golden hour — quyosh botishi

Maslahat:

Har bir kadr — bitta gap (bitta prompt). Murakkab sahna kerak bo'lsa — bir necha kadrga bo'ling.

YouTube'da "cinematography terms" qidiring — bepul o'rganasiz.

Ertaga — Veo uchun promptlar.""",

    # ========== ПОСТ 13 — Промпты Veo ==========
    """🎥 Veo uchun promptlar — hikoyali

Hurmatli do'stlar, Veo 3.1 boshqalardan farqli — u uzun va batafsil promptlarni yaxshi tushunadi.

Veo uchun maslahatlar:

✨ 100-300 so'z prompt yozish mumkin
Boshqa modellar 50 so'zdan keyin chalkashadi. Veo — yo'q.

✨ Hikoya tuzilishi muhim
Avval umumiy sahna, keyin tafsilotlar.

✨ Bosqichma-bosqich tasvirlang
Birinchi sahna → kim → nima qilyapti → atmosfera → kamera.

✨ Hissiyotlar va kayfiyat
"Nostalgic", "uplifting", "tense" — Veo buni hisobga oladi.

✨ Native ovoz
Promptda dialog yozsangiz, lablar sinxronlashadi (ingliz, ispan).

Misol struktura:

[SAHNA]: A young entrepreneur in modern coworking space
[HARAKAT]: opens laptop, smiles at the screen, types
[ATMOSFERA]: bright morning, warm coffee on desk, plants nearby
[KAMERA]: medium shot, slow push in, shallow depth of field
[YORUG'LIK]: natural daylight through window
[OVOZ]: ambient cafe sounds, soft typing

Bu Veo uchun ideal struktura.

Aniq promptlar Instagramda DM yozsangiz — gaplashamiz.

Ertaga — bepul kreditlar.""",

    # ========== ПОСТ 14 — Бесплатные кредиты ==========
    """🆓 Bepul AI-video kreditlari — qayerdan?

Hurmatli do'stlar, endi qiziq qism — qayerdan tekin video olish mumkin.

Mavjud bepul variantlar (may 2026):

1. KLING — eng saxiy
66 kredit har kuni, kreditkasiz. Sinovlar uchun zo'r.

2. RUNWAY — bir martalik
Boshlang'ich 125 kredit. Ko'p emas, lekin tatib ko'rish uchun yetadi.

3. PIKA — boshlang'ich + kunlik
30 kredit boshlanishida + har kuni kichik bonus.

4. HAILUO — saxiy boshlanish
Ko'p bepul kreditlar boshida. Bir-ikki hafta o'ynash mumkin.

5. LUMA Dream Machine
Har kuni bir nechta tekin generatsiya beradi.

6. HIGGSFIELD — boshlang'ich
75 kredit boshida. Tatib ko'rish uchun yetadi.

Maslahatlar:

• Bir necha xizmatda ro'yxatdan o'ting — kreditlarni jamlaysiz
• Eng ko'p tekin — Kling. Undan boshlang.
• Tijoriy ishlatish: bepul tarif ko'pincha ruxsat etmaydi
• Watermark (suv belgisi) — bepulda bo'lishi mumkin

⚠️ Diqqat: bu raqamlar tez-tez o'zgaradi. Kompaniyalar siyosatini o'zgartiryapti.

Ertaga — uzun video qanday qilish.""",

    # ========== ПОСТ 15 — Длинное видео ==========
    """⏱️ Uzun AI-video qanday qilish

Hurmatli do'stlar, AI-modellar 5-15 sekundlik videolar qiladi. Lekin uzun videolar ham mumkin.

Asosiy texnika — birlashtirish:

1. SCENARIY tuzing
60 sekundlik video uchun 6-8 ta sahna kerak. Har biri 8-10 sek.

2. HER SAHNANI alohida generatsiya qiling
Aynan bir AI-modelda, bir uslubda — tutashtirish oson bo'lishi uchun.

3. PERSONAJ CONSISTENCY
Bir odam turli sahnalarda — bir xil ko'rinishda. Reference image yordam beradi.

4. CapCut yoki PREMIERE'da yig'ish
Klipni ulang, transition qo'shing, ovoz qo'shing.

5. MUSIQA va OVOZ
ElevenLabs — ovoz uchun. Suno — musiqa uchun. CapCut'da o'zining ham bor.

Maslahatlar:

✅ Sahnalar orasida tabiiy transition
✅ Bir xil yorug'lik va palitra
✅ Bir xil personaj kiyimi
✅ Musiqa hamma sahnalarda davom etadi

❌ Uzunlik xato:
60 sek dan ortig'i — TikTok va Reels uchun ko'p. Optimal — 15-30 sek.

Ertaga — AI-videoga ovoz qo'shish.""",

    # ========== ПОСТ 16 — Звук в видео ==========
    """🔊 AI-videoga ovoz qo'shish

Hurmatli do'stlar, ko'pincha AI-video sukut bilan chiqadi. Ovoz qo'shish kerak.

3 turdagi ovoz:

1. OZVUCHKA (voiceover)
Matn → ovoz. Reklama, hikoya uchun.
Eng yaxshi: ElevenLabs.

2. MUSIQA (background)
Sahnani jonlantiradi.
Eng yaxshi: Suno, Udio.

3. EFFEKTLAR (sound effects)
Eshik ovozi, suv shovqini, qadamlar.
Eng yaxshi: ElevenLabs SFX, freesound.org.

Workflow:

1. AI-video generatsiya qiling (sukut)
2. ElevenLabs'da matnga ovoz yarating
3. CapCut yoki Premiere'da birlashtiring
4. Musiqa va effektlar qo'shing
5. Balansni sozlang (ovoz balandroq, musiqa pastroq)

Native ovozli modellar:

✅ Kling 3.0 — 5 tilda
✅ Veo 3.1 — ingliz, ispan
❌ Runway — ovoz yo'q (alohida qo'shish kerak)
❌ Pika — ko'p hollarda yo'q

Maslahat:

Native ovoz har doim emas yaxshi. Ba'zan ElevenLabs'dan alohida qo'shish — sifatliroq.

Ertaga — ElevenLabs haqida batafsil.""",

    # ========== ПОСТ 17 — ElevenLabs ==========
    """🎤 ElevenLabs — AI ovozlar №1

Hurmatli do'stlar, ElevenLabs — ovoz dunyosini o'zgartirgan vosita.

Nima qila oladi:

✨ Matn-ovoz
Yozasiz — odam kabi gapiradi. Hech kim AI ekanini sezmaydi.

✨ 32 tilda ovoz
Inglizcha, ispan, fransuz, koreys va boshqalar. Uzbek hozircha yo'q.

✨ Voice Cloning
O'z ovozingizdan 1 daqiqalik klip yuborsangiz — uni klon qiladi.

✨ Speech-to-Speech
Bir ovozdan boshqaga o'zgartirish. Audio sifat saqlanadi.

✨ Multilingual v2
Bir ovoz — barcha tillarda gapira oladi.

✨ Sound Effects
Tabiat ovozlari, mexanika, jangchi — generatsiya qiladi.

Kim uchun yaxshi:

• Reklama ozvuchkasi
• Audiokitablar
• YouTube videolar
• Podkastlar
• Brending videolari
• AI-aktyorlar uchun

Bepul tarif:
10,000 belgi har oy — sinab ko'rish uchun yetadi.

Maslahat:

Uzbek tilida hozircha to'g'ridan-to'g'ri ishlamaydi. Lekin Speech-to-Speech orqali — o'zingiz uzbek matnni gapirib yozasiz, ElevenLabs uni "boshqa odam" ovoziga o'zgartiradi.

Ertaga — uzbek tilida ovoz.""",

    # ========== ПОСТ 18 — Узбекская озвучка ==========
    """🇺🇿 Uzbek tilida AI-ovoz

Hurmatli do'stlar, eng ko'p so'raydigan savol — AI uzbek tilida gapira oladimi?

Hozirgi holatda:

❌ ElevenLabs to'g'ridan-to'g'ri uzbek tilini bilmaydi
❌ Google TTS uzbek tilida bor, lekin sifat past
❌ OpenAI uzbek tilini gapiradi, lekin aksent yo'q

Mavjud yechimlar:

1. Speech-to-Speech (ElevenLabs)
O'zingiz uzbek tilida o'qib yozasiz. ElevenLabs uni "boshqa odam" ovoziga o'zgartiradi. Talaffuz va akcent saqlanadi.

2. Yandex SpeechKit
Uzbek tilini biladi. Sifat o'rtacha — yangiliklar uchun yetarli.

3. Microsoft Azure
Uzbek ovozlari bor, narxi qulay.

4. Cloud-based servicelar (yandex.cloud, yandex.speechkit)
O'rta sifatli, lekin ishlaydi.

Yangi xabar:

Bir necha kompaniya 2026-yil oxirigacha uzbek tilini qo'shishni va'da qildi. Bu yo'nalishda harakatlar bor.

Mening usulim:

Uzbek tilida video uchun — o'zim gapirib yozaman, keyin ElevenLabs orqali ovozimni boshqa ovozga o'zgartiraman. Akcent qoladi, sifat baland.

Ertaga — CapCut va AI haqida.""",

    # ========== ПОСТ 19 — CapCut для AI-видео ==========
    """🎞️ CapCut — AI-video uchun zo'r vosita

Hurmatli do'stlar, CapCut — tekin va kuchli montaj dasturi. AI-video bilan ishlaganda ajoyib.

CapCut'da nima qilish mumkin:

✨ AI-video birlashtirish
Bir necha Kling/Runway klipni qo'shasiz, transitions qo'yasiz.

✨ Avtomatik subtitr
AI ovozni eshitadi va matn yaratadi — uzbek tilida ham.

✨ AI Speech
Matn yozasiz, CapCut uni o'qiydi. Tekin TTS.

✨ Auto Captions
Subtitrlarni avtomatik joylashtiradi.

✨ Effektlar va transitions
Yuzlab tekin effekt — Pika'siz ham viral video qilish mumkin.

✨ Format uchun moslash
TikTok 9:16, YouTube 16:9, Instagram 1:1 — bir bosishda.

CapCut Pro:

Yiliga $80 atrofida. Watermark yo'q, kengaytirilgan funksiyalar.

Maslahatlar:

• Tekin versiya 90% ishlarni qiladi
• Premium kerak emas — tajriba ortgach o'ylab ko'ring
• Klaviatura yorliqlari o'rganing — 5x tezroq ishlaysiz
• Templatelar — viral video tezkor

Workflow:

1. AI-modeldan video oling
2. ElevenLabs'da ovoz tayyorlang
3. CapCut'da birlashtiring
4. Subtitr va musiqa qo'shing
5. Export va publikatsiya

Ertaga — TikTok va Reels uchun video formatlari.""",

    # ========== ПОСТ 20 — Размеры видео ==========
    """📐 AI-video formatlari — qaysi qaerda

Hurmatli do'stlar, har bir platforma uchun o'z format kerak.

TIKTOK:
• 9:16 vertikal
• 1080x1920 px
• 15-60 sek optimal
• Format: MP4

INSTAGRAM REELS:
• 9:16 vertikal
• 1080x1920 px
• 15-90 sek
• Format: MP4

INSTAGRAM POST:
• 1:1 kvadrat yoki 4:5 vertikal
• 1080x1080 yoki 1080x1350 px
• 60 sek gacha

INSTAGRAM STORIES:
• 9:16 vertikal
• 1080x1920 px
• 15 sek (avtomatik bo'linadi)

YOUTUBE:
• 16:9 gorizontal
• 1920x1080 px (HD) yoki 3840x2160 (4K)
• Cheklov yo'q

YOUTUBE SHORTS:
• 9:16 vertikal
• 1080x1920 px
• 60 sek gacha

TELEGRAM:
• Har qanday format
• Lekin gorizontal yaxshi ko'rinadi

Asosiy maslahat:

Bitta video uchun bir necha format tayyorlang. Bir AI-generatsiyadan CapCut'da qaytatdan kropp qilib bir necha format chiqaring.

Ertaga — birinchi 3 sekundning sehri (Hook).""",

    # ========== ПОСТ 21 — Hook ==========
    """🎯 Birinchi 3 sekund — eng muhim

Hurmatli do'stlar, AI-videongiz qanchalik yaxshi bo'lmasin, agar birinchi 3 sekundda tomoshabin to'xtamasa — hammasi behuda.

Bu — HOOK (qarmoq).

Yaxshi Hook'ning xususiyatlari:

1. SAVOL beradi
"Bu nima bo'lishi mumkin?" deb o'ylatadi.

2. KO'Z UCHUN qiziq
Yorqin rang, kutilmagan harakat, sirli obyekt.

3. SHOK QILADI
"Voy", "vau" — yurakni ushlaydi.

4. AYTILMAGAN VAdir
"Bilmasangiz — ko'rasiz" — qiziqish hosil qiladi.

5. TANIDA TANISH
"Bu meniki!" — tomoshabin o'zini taniydi.

AI-video uchun Hook namunalari:

❌ Yomon:
Video oddiy boshlanadi, normal sahna, sekin rivojlanadi.

✅ Yaxshi:
- Yuqori burchakdan tushish (zoom in)
- Kutilmagan obyekt (cherry yiqilyapti)
- Yorqin yorug'lik portlashi
- Yuz juda yaqin kadr
- Tez harakatlanuvchi obyekt to'satdan to'xtaydi

Texnik maslahat:

CapCut'da videoni boshidan 1-2 sekund cropp qiling — agar boshi kuchli emas. Yoki AI'da yangidan generatsiya qiling — kuchli boshlanishni so'rab.

Ertaga — AI-video e-commerce uchun.""",

    # ========== ПОСТ 22 — E-commerce ==========
    """🛍️ AI-video e-commerce uchun

Hurmatli do'stlar, internet do'kon egalari — sizlar uchun zo'r imkoniyat.

E-commerce uchun AI-video qilish mumkin:

1. MAHSULOT 360°
Mahsulot atrofida aylanish — har tomondan ko'rsatish. Kling yoki Runway zo'r qiladi.

2. LIFESTYLE
Mahsulot kundalik hayotda — odam kiyganda, foydalanganda. Veo'da yaxshi chiqadi.

3. UNBOXING
AI bilan unboxing video — paket ochilyapti, mahsulot chiqyapti. Higgsfield zo'r.

4. BEFORE/AFTER
Mahsulot oldidan va keyin — kosmetika, kiyim, mebel uchun.

5. KUNDALIK ROUTINE
"Bir kun mening mahsulotim bilan" — sahnali video, hayotni jonli ko'rsatish.

6. TESTIMONIAL (sharhlar)
AI-aktyor sharhi — kelajakdagi yo'nalish (HeyGen va boshqa avatarlar).

Sotuvni oshiruvchi elementlar:

✅ Mahsulot rangini aniq ko'rsating
✅ Tafsilotlar yaqin kadr
✅ Foydalanish jarayoni
✅ Mahsulot o'lchami (qo'l bilan solishtirish)
✅ Narx va aksiyalar — kadrda yozilgan

Maslahat:

Kichik do'kon uchun AI-video — Instagramda 10x ko'proq diqqat tortadi. Foto'larni almashtirib chiqing.

Ertaga — xizmatlar uchun AI-video.""",

    # ========== ПОСТ 23 — Услуги ==========
    """💼 AI-video xizmatlar biznesi uchun

Hurmatli do'stlar, salon, klinika, ta'lim — barchasiga AI-video kerak.

GO'ZALLIK SALONLARI uchun:

• Xizmatlar before/after — yuz, soch
• "Bir kun salonda" — atmosfera, mijozlar
• Master haqida — uning ishi yaqin kadr
• Yangi xizmatlar reklamasi

KLINIKALAR uchun:

• Klinika ichidan ekskursiya — tinch va ishonchli
• Vrachlar tanishtirish — AI-rasm + harakat
• Protseduralar tushuntirish — vizualizatsiya
• Mijozlar his-tuyg'usi (sog'lom va xursand)

TA'LIM MARKAZLARI uchun:

• Talabalar muvaffaqiyati
• Dars jarayoni jonli
• Domla taqdimi
• Kursdan keyin natija

RESTORANLAR uchun:

• Taom tayyorlash jarayoni — appetit hosil qiladi
• Atmosfera — sham, samimiy yorug'lik
• Ofitsiantlar va xizmat
• Mavsumiy menyu reklamalari

UMUMIY XIZMATLAR uchun:

• Mijoz uchun yechim — muammodan natijaga
• Ish jarayoni — siz nima qilasiz
• Ishonch — yillar tajriba, sertifikatlar
• Kontakt — qanday qilib siz bilan bog'lanish

Maslahat:

Xizmatlar uchun "hissiyot" muhim. Faqat ish ko'rsatish kifoya emas — odam o'zini ko'rsin: xursand, ishonchli, sog'lom.

Ertaga — kiyim do'konlari uchun.""",

    # ========== ПОСТ 24 — Одежда ==========
    """👗 AI-video kiyim brendlari uchun

Hurmatli do'stlar, kiyim do'koni — eng tez foyda olishi mumkin bo'lgan biznes AI-video bilan.

Nima uchun?

❌ Eski usul: model, fotograf, studio, kun ish, $500+
✅ Yangi usul: AI-model, 30 daqiqa, $20-50

AI-video kiyim uchun:

1. LOOKBOOK
Bir model — 10 ta kiyim. AI bir yuzni saqlaydi, kiyimni o'zgartiradi.

2. STREET STYLE
Model ko'chada yuradi, atrof o'zgaradi (kafe, park, do'kon).

3. KIYIMNI HARAKATDA
Kiyim shamolda uchadi, etak aylanadi — Kling buni zo'r qiladi.

4. TAFSILOTLAR YAQIN KADR
Tikilish, mato, accessuar — yaqin kadr kerak.

5. MAVSUMIY KAMPANIYA
Yoz/qish/kuz/bahor — har biri uchun atmosfera.

6. TRANSFORMATSIYA
"Avval — keyin" — kiyim almashtirilgach o'zgaruvchi taassurot.

Texnik maslahat:

✅ Kiyim uchun Kling — eng yaxshi
✅ Kataloglar uchun Midjourney (statik rasm) + Kling (harakat)
✅ Reklama uchun Veo (sifat)
✅ Sosial tarmoq uchun Pika (tezlik)

Sotuv oshirish:

• Kiyim narxini ko'rsating
• O'lchamlar (S/M/L) yozing
• Materialni aniq ayting
• Yetkazib berish vaqti

Ertaga — restoran va ovqat uchun AI-video.""",

    # ========== ПОСТ 25 — Еда ==========
    """🍔 AI-video oziq-ovqat va restoran uchun

Hurmatli do'stlar, ovqat reklamasi — eng qiyin va eng kuchli yo'nalish.

Nima uchun qiyin:

❌ Ovqat AI'da ba'zan "plastik" ko'rinadi
❌ Tafsilotlar buziladi
❌ Realizm muhim — soxta ovqat ko'rinmasligi kerak

Nima ishlaydi:

✅ Issiq taom bug'i — Kling realistik qiladi
✅ Suyuqliklar quyilishi — Kling zo'r
✅ Yaqin kadr (macro) — Veo va Runway
✅ Atmosfera (samimiy yorug'lik) — Luma

AI-video restoran uchun:

1. TAOM TAYYORLASH
Oshxonada master ovqat qiladi — appetit hosil qiladi.

2. TAOMNI YAQIN KADR
Buyumning eng yaxshi tomoni — to'yintirilgan rang.

3. MIJOZ TAJRIBA
Stol, sham, tabassum, lazzat.

4. MAVSUMIY MENYU
Yoz uchun salat, qish uchun sho'rva.

5. YETKAZIB BERISH
Paket ochilyapti, taom issiq.

Maslahatlar:

✅ Promptda "appetizing", "fresh", "steaming hot" yozing
✅ Yorug'lik — har doim warm (issiq tonlar)
✅ Yaqin kadr ko'p qiling
✅ Real foto bilan AI ni aralashtiring (Midjourney + Kling)

Misol:

"Close-up macro shot of fresh hot lagman, steam rising, golden warm lighting, shallow depth of field, slow camera push in"

Ertaga — yangi boshlovchilar xatolari.""",

    # ========== ПОСТ 26 — Ошибки новичков ==========
    """⚠️ AI-video xatolari — yangi boshlovchilar

Hurmatli do'stlar, ko'p odam AI-video qilishni boshlaydi, lekin natija — yomon. Sabablar:

XATO 1: Juda murakkab prompt
Yangi boshlovchi 200 ta tafsilot yozadi — AI chalkashadi.
✅ To'g'ri: 30-50 so'z, asosiy elementlar.

XATO 2: Real bo'lmagan kutilma
"Iron Man futbolda Messi bilan" — AI buni qila olmaydi.
✅ To'g'ri: real bo'lishi mumkin sahnalar.

XATO 3: Bir generatsiyadan voz kechmaslik
Birinchi natija yomon — odam tashlab ketadi.
✅ To'g'ri: 3-5 marta sinab ko'ring. Promptni o'zgartiring.

XATO 4: Sifat va format aralash
4K kerak emas bo'lsa, 720p generatsiya qiling — tezroq va arzonroq.

XATO 5: Bir modelga yopishish
Hammasiga Runway ishlatish — qimmat va sekin. Har vazifaga o'z modeli bor.

XATO 6: Ovoz unutilgan
AI-video sukut bilan chiqadi. Odamlar uchun bu g'alati.
✅ To'g'ri: ElevenLabs yoki CapCut'da ovoz qo'shing.

XATO 7: Hook yo'q
Birinchi 3 sekund oddiy — tomoshabin keladi va ketadi.

XATO 8: Hashtag noto'g'ri
Bo'sh hashtaglar ishlatish — natija yo'q.
✅ To'g'ri: ishlovchi hashtaglar tekshirib qo'shing.

XATO 9: Bir formatga yopishish
TikTok'ga gorizontal video qo'yish — yo'qoladi.

XATO 10: Hech kim ko'rmaydi deb tushib ketish
Birinchi videolar — eng oddiy. Davom eting.

Ertaga — AI-video bilan qancha pul ishlash mumkin.""",

    # ========== ПОСТ 27 — Сколько стоит AI-видео ==========
    """💰 AI-video qancha turadi mijozlar uchun

Hurmatli do'stlar, ko'p odam so'raydi — AI-video reklamasi qancha turadi?

Bozor narxlari (may 2026):

❌ Past narx (don't be cheap):
$10-30 per video — bu yomon. Ishlamaydi.

✅ Yangi boshlovchilar uchun:
$50-100 per 15 sek video
Bu — birinchi mijozlar uchun. Kafolat va portfel uchun.

✅ O'rta darajadagi:
$100-300 per video
1-2 yil tajriba, yaxshi portfel.

✅ Professional:
$300-800 per video
3+ yil tajriba, brend mijozlar.

✅ Yuqori darajadagi:
$800-3000 per kampaniya
Reklama agentligi, katta brendlar.

Nima mijoz to'laydi:

1. Vaqt — sizning soatlar
2. Tajriba — siz nimani bilasiz
3. Vositalar — Midjourney, Kling, Runway obunalar
4. Natija — mijoz nima oladi (sotuvlar)

Maslahatlar:

✅ Birinchi 3-5 mijozni arzonga oling — portfel uchun
✅ Keyin narxni oshiring — har 2-3 oyda
✅ Paket sotish (3 video, 5 video) — yagona videodan ko'p
✅ Oylik shartnomalar — eng yaxshi (regular income)

Mijoz qidirish:

• Upwork — AI-video creator
• Fiverr — AI ad maker
• LinkedIn — to'g'ridan-to'g'ri marketing directors
• Mahalliy biznes — Telegram, Instagram

Ertaga — AI-video trendlari 2026.""",

    # ========== ПОСТ 28 — Тренды 2026 ==========
    """🚀 AI-video trendlari — 2026

Hurmatli do'stlar, bozor tez o'zgaryapti. Bugun — nima trend.

TREND 1: Native ovoz
Veo va Kling endi videoda ovoz qo'shadi. Bu standart bo'lyapti.

TREND 2: Uzun videolar
5-15 sek emas, 30-60 sek native. Modellar yoqimliroq sahnalar yaratadi.

TREND 3: Character consistency
Bir personaj — turli sahnalarda bir xil. Bu reklama uchun katta yutuq.

TREND 4: Multi-shot stories
Bitta promptdan butun hikoya. Kling 3.0 bu yo'nalishda lider.

TREND 5: 4K va vertikal
TikTok va Reels uchun darhol tayyor format.

TREND 6: AI + real foto
Murakkab kompozitsiya — odam asl, fon AI, mahsulot real. Bu eng kuchli kombinatsiya.

TREND 7: Avatarlar va gapiruvchi boshlar
HeyGen, Synthesia, Hedra — yangi yo'nalish. (Bu haqda keyingi oyda batafsil yozaman).

TREND 8: Open-source modellar
Wan, LTX — kompyuteringizga o'rnatib, bepul ishlash. Texnik odamlar uchun.

TREND 9: AI-stylization
Bir uslubda hammasi — brending uchun zo'r.

TREND 10: Real-time generation
Hozircha sekin, 2027 yilgacha — real-time bo'ladi. Hammasi o'zgaradi.

Maslahat:

Trendlarni kuzating, lekin asosiy ko'nikmangizga e'tibor bering. Yangi modellar har oy chiqadi — hammasini o'rganish kerakmas.

Ertaga — qaerdan boshlash kerak (yangi boshlovchilar uchun).""",

    # ========== ПОСТ 29 — Откуда начать ==========
    """🎯 AI-video — qaerdan boshlash kerak

Hurmatli do'stlar, ko'p odam so'raydi: men buni qila olmayman, juda murakkab. Yolg'on. Boshlash oson.

Birinchi hafta — bepul boshlash:

1-kun: Kling'da ro'yxatdan o'ting (66 kredit/kun bepul)
2-kun: Birinchi videoni qiling — eng oddiy
3-kun: Yana 5-10 ta sinab ko'ring
4-kun: ChatGPT bilan promptlar yozing
5-kun: CapCut'ni yuklang
6-kun: AI-videoni CapCut'ga import qiling
7-kun: Birinchi muvaffaqiyatli videoni sosial tarmoqqa qo'ying

Ikkinchi hafta — kengaytirish:

• Yangi modellar sinab ko'ring (Pika, Hailuo)
• ElevenLabs'da ovoz qo'shing
• Subtitr o'rganing
• 5-10 video yarating

Uchinchi hafta — qiyinroq:

• Personaj yaratish (Midjourney + Kling)
• Multi-shot hikoyalar
• Reklama uchun video
• Birinchi mijozni topish

To'rtinchi hafta — pul ishlash:

• Portfel sahifasi
• Instagram va TikTok'da postlash
• Birinchi mijozga $50 ga video
• Sharhlar yig'ish

Asosiy maslahatlar:

✅ Kuniga 30-60 daqiqa kifoya
✅ Birinchi videolarni saqlang — keyin ko'rasiz qancha o'sgansiz
✅ Boshqalar bilan solishtirmang — har kim o'z tezligida
✅ Yomon natijalardan qo'rqmang — bular o'rganish qismi

Mukammallikni kutmang. Boshlang. Yo'lda o'rganasiz.

Ertaga — seriyaning yakuni.""",

    # ========== ПОСТ 30 — Итог серии ==========
    """🎬 AI-video seriyasi yakunlandi

Hurmatli do'stlar, 30 kun davomida AI-video haqida hamma narsani o'rgandik.

Biz qamradik:

✅ 7 ta asosiy AI-video model (Kling, Runway, Veo, Pika, Luma, Hailuo, Higgsfield)
✅ Har birining afzalliklari va kamchiliklari
✅ Promptlar yozish — har bir modelga
✅ Bepul kreditlar — qayerdan olish
✅ Uzun video qilish
✅ Ovoz va musiqa qo'shish
✅ CapCut'da montaj
✅ Formatlar va o'lchamlar
✅ Hook — birinchi 3 sek sehri
✅ Biznes uchun video (kiyim, ovqat, salon, klinika)
✅ Yangi boshlovchilar xatolari
✅ Narxlar va trendlar

Endi siz bilasiz:

→ Qanday modelni qachon ishlatish
→ Qanday qilib professional natija olish
→ Qaerdan boshlash va qancha pul ishlash mumkin

Keyingi oy:

AI-avatarlar haqida butun seriya. HeyGen, Synthesia, Hedra, Tavus va boshqalar. Gapiruvchi boshlar, virtual aktyorlar.

Endi savol:

Sizda eng katta savol nima bo'ldi? Sharhlarda yozing — keyingi haftada javob beraman.

Va — siz bu bilim bilan birinchi videoyingizni qilingmi? Halol javob bering 😊

Rahmat hammangizga — birga o'rgandik.""",
]


# ============================================
# 30 ДНЕВНЫХ ПОСТОВ (17:00) — про AI и будущее
# ============================================

DAILY_AI_POSTS = [
    """🤖 AI har kuni odamlarni ishdan ozod qilyapti

Microsoft 6000 ishchini ishdan bo'shatdi — yarmi AI bilan almashtirildi.

Coca-Cola endi reklama uchun kamera olmaydi. Klarna 700 ta operatorni AI bilan almashtirdi — yiliga $40 mln tejadi.

Bu fantaziya emas, bu bugun.

Siz tayyormisiz?""",

    """💼 5 yil ichida bu kasblar yo'qoladi

Tadqiqotlar ko'rsatadi: 2030 yilgacha 300 mln ish o'rni AI tomonidan almashtirilishi mumkin.

Birinchi navbatda yo'qoladi:
- Call-center operatorlari
- Tarjimonlar
- Oddiy dizayn
- Buxgalterlar
- Maslahatchilar

Lekin yangilari ham paydo bo'ladi: AI-mutaxassis, prompt engineer, AI-content creator.

Endi savol: siz qaysi tomondamisiz?""",

    """🎬 Bir reklama — 10 daqiqada

Ilgari reklama tayyorlash uchun kerak edi:
- Kameralar
- Modellar
- Studiya
- 3-5 kun ish
- $1000-5000

Bugun: AI bilan bir kishi 10 daqiqada qiladi. Narxi — $20-50.

Bu inqilob. Mayda biznes endi katta brendlar kabi reklama qila oladi.""",

    """🧠 AI bilan ishlash — yangi savod

100 yil oldin o'qish-yozishni bilmaganlar quldek ishlashga majbur edi.
50 yil oldin kompyuterni bilmagan — yaxshi ish topa olmadi.
Bugun AI'ni bilmagan — ertaga ortda qoladi.

Bu juda jiddiy.

AI — bu kelajak savodi. Hozir o'rganmasangiz — keyin kech bo'ladi.""",

    """🚀 Bir yilda $100 mln — 8 kishi bilan

Cursor — AI-kod yozish vositasi. 8 kishilik jamoa.

Yiliga $100 mln daromad keltiryapti.

Eski dunyoda buni qilish uchun 5000 kishi kerak edi. Yangi dunyoda — AI bilan ozgina jamoa hammasini qiladi.

Bu yangi haqiqat.""",

    """🎨 AI rassom — endi haqiqat

Bir necha yil oldin rassom bo'lish uchun:
- Yillar o'qish
- Qimmat materiallar
- Hamma uslublarni egallash

Bugun: Midjourney, Flux, Nano Banana orqali har qanday rasm — bir necha soniyada.

Asl rassomlar yo'qolmaydi — ular AI bilan tezroq ishlashni o'rganadilar.""",

    """📈 Uzbekistanda AI — bo'sh bozor

Rossiya, Qozog'iston AI bo'yicha oldinda. Uzbekistanda esa bu bozor hali bo'sh.

Bu sizning katta imkoniyatingiz.

Birinchi bo'lganlar eng yaxshi joyni egallaydi.

Hozir boshlang. Keyin kech bo'ladi.""",

    """⚡ AI 24/7 ishlaydi

Bizning bot kanalimda har kuni o'zi post yozadi.
Men uxlayman — u ishlaydi.
Men bola bilan band — u ishlaydi.

Bu AI'ning qudrati. U charchamaydi, kasal bo'lmaydi.

Tasavvur qiling: sizning biznesingizda AI 24/7 mijozlarga javob beradi, sotuvlarni kuzatadi.

Bu — bugun.""",

    """💰 AI bilan qancha pul ishlash mumkin?

Realiy raqamlar:
- AI-content creator: oyiga $500-3000
- AI-prompt engineer: $2000-8000
- AI-yechimlar mutaxassisi: $3000-15000
- AI bilan biznes egasi: cheklov yo'q

Hammasi sizdan boshlanadi. Kim oldin o'rgansa — oldin pul ishlaydi.""",

    """🎯 Bolangizni AI'ga o'rgating

Bizning bolalarimiz AI bilan birga o'sadi.

5-7 yoshdan boshlab AI bilan "do'stlashish" mumkin:
- ChatGPT bilan suhbat
- Midjourney bilan rasm chizish
- AI bilan ertak yozish

Bu bolaning miyasini boshqacha rivojlantiradi.""",

    """🏭 Robot zavodlar — endi haqiqat

Amazon omborlarida 75% ish robotlar va AI tomonidan bajariladi.

Foydasi:
- 24/7 ishlash
- Xato kam
- Kasal bo'lmaydi

Bu jarayon to'xtatib bo'lmaydi. Bizga moslashish kerak.""",

    """📱 Reklama yaratish — endi telefonda

Ilgari professional reklama uchun:
- Premiere Pro
- After Effects
- Photoshop
- Yillik o'qish

Bugun: telefonda Midjourney + Kling + CapCut = professional reklama bir soatda.""",

    """🌍 Dunyodagi eng yosh million doller

22 yoshli yigit AI bilan ilovachalar yaratdi. Bir yilda $1 mln. Yolg'iz.

19 yoshli qiz AI-content agency ochdi. 6 oyda $500,000 daromad.

Yosh muhim emas. Eng muhimi — boshlash. Bugun.""",

    """🔥 ChatGPT haftada 800 mln foydalanuvchi

Bu jahonning 10% odamlari.

Tarixda hech bir texnologiya bunchalik tez tarqalmagan.

Internet 7 yil kerak edi 100 mln foydalanuvchiga.
ChatGPT — 2 oy.

Tayyormisiz?""",

    """🎓 Universitet o'qish endi shartmi?

Sam Altman (OpenAI rahbari) dedi: "Yaqinda universitet diplomi ishga qabul qilishda muhim bo'lmaydi".

Nima muhim bo'ladi?
- AI bilan ishlash qobiliyati
- Tezda o'rganish
- Real loyihalar

Qiyin savol. Lekin javob shu yerda.""",

    """💻 AI dasturlash o'rganishni qulay qildi

Ilgari dasturlash o'rganish uchun:
- 2-3 yil
- Yuzlab kitoblar
- Yuqori matematika

Bugun: ChatGPT yoki Claude bilan har qanday odam dastur yoza oladi.

"Men texnik odam emasman" — endi bahona emas.""",

    """🎬 Hollywoodga zarba — AI kino yaratyapti

OpenAI Sora yaratdi va keyin yopdi. Boshqa modellar paydo bo'ldi — Kling, Veo, Runway.

Hollywood larzaga keldi. Aktyorlar ish tashladilar.

Bir kino yaratish endi millionlik byudjet emas — bir necha ming dollar.

Texnologiya hech kimni so'ramaydi. U keladi.""",

    """🧘 AI siz uchun terapevtmi?

40% yoshlar endi terapevtga ChatGPT'ni afzal ko'ryaptilar.

Sabab:
- Tekin
- Hech qanday baholash yo'q
- Har doim mavjud
- Sirni saqlaydi

Bu yaxshimi? Murakkab savol. Lekin haqiqat shu — AI bizning ruhiy sog'lig'imizga ham ta'sir qilyapti.""",

    """⏰ "Vaqtim yo'q" — endi bahona emas

AI shu uchun yaratildi — vaqtni tejash.

Elektron pochta yozish 30 daqiqamiz? ChatGPT — 30 soniyada.
Yangiliklar o'qish 1 soat? AI xulosa qiladi — 5 daqiqada.

"Men band" — endi AI'ni o'rganmagan odamning belgisi.""",

    """🎯 5 ta AI vosita har kuni ishlatyapman

1. ChatGPT — yozish va o'ylash
2. Claude — uzun matnlar
3. Midjourney — rasmlar
4. Kling — videolar
5. ElevenLabs — ovoz

Bu mening "ofisim". Har biri 1-2 yil oldin yo'q edi.

5 yildan keyin yana qanchalar paydo bo'ladi?""",

    """🌱 Onalar AI bilan biznes yaratyapti

Men shaxsan dekretdaman. Bir vaqtning o'zida:
- Bolam bilan vaqt o'tkazaman
- AI-content ishlab chiqaman
- Brendlar uchun reklamalar yarataman

Bu AI'siz mumkin emas edi. Onalar — yangi kuch.""",

    """💡 Eng katta xato — kutish

Ko'p odam aytadi: "Men keyinroq boshlayman. Hozir vaqt yo'q."

"Keyinroq" hech qachon kelmaydi.

AI har kuni yangilanadi. Siz kutgan sari — masofa o'sadi.

Eng yaxshi vaqt — bugun.""",

    """🤖 Robotlar oilada — uzoq emas

Tesla, Figure, Boston Dynamics — humanoid robotlar yaratyaptilar.

Narxlar 2027-2028 yilga $20,000-30,000 ga tushadi. Bu — mashina narxi.

5-7 yil ichida har bir o'rtacha oila uchun mavjud bo'ladi.

Tayyormisiz?""",

    """📊 AI sizning fikrlashingizni o'zgartiradi

Yangi tadqiqot: AI bilan muntazam ishlovchi odamlar:
- Tezroq qaror qabul qiladilar
- Ko'proq variantlarni ko'radilar
- Kreativ fikrlay boshlaydilar
- Stress kamayadi

Sizning fikrlashingizning sifati — sizning hayotingiz sifati.""",

    """🚨 Eng katta xavf — AI'ni o'rganmaslik

Ko'pchilik AI'dan qo'rqadi: "U mening ishimni oladi".

Haqiqat: AI sizning ishingizni olmaydi. AI'ni o'rgangan odam — siznikini oladi.

Bu boshqa narsa.

Tanlov sizniki.""",

    """🌟 Uzbekistan o'qishi kerak

Hindiston 2025'da $1 mlrd AI'ga sarfladi.
Qozog'iston AI bo'yicha milliy strategiya qabul qildi.

Uzbekistanda bu sizning imkoniyatingiz. Birinchi bo'lganlar — yutadilar.

Davlatdan kutmasdan — o'zingiz boshlang.""",

    """🎤 AI ovozlari — endi tabiiy

ElevenLabs AI ovozni shunchalik yaxshi qildi, hatto odamlar farqlay olmayapti.

Bu nima degani?
- Audio kontent — har kim yarata oladi
- Tarjimonlik — AI qiladi
- Audiokitablar — bir kishi yarata oladi
- Podkastlar — yarim narxda

Bu inqilob hozir sodir bo'lyapti.""",

    """🏆 Eng katta sirim — har kuni o'rganish

Ko'p odam so'raydi: "Qanday qilib AI bilan ishni boshladingiz?"

Javob: har kuni yangi narsa o'rganaman.

15 daqiqa. 30 daqiqa. Soat.

Bu kichik — lekin bir yilda 100 soat. Va 100 soat — siz mutaxassis bo'lasiz.

Sizning rejangiz bormi?""",

    """🌅 Boshlash uchun hech qachon kech emas

50 yoshli ayol AI bilan ishlay boshladi. Endi $5000 oyiga ishlaydi.

70 yoshli pensioner ChatGPT bilan kitob yozdi. Bestseller.

Yosh muhim emas. Faqat istak muhim.

Boshlang. Birinchi qadam — eng qiyini, lekin eng muhimi.""",

    """💪 AI sizning superkuchingiz

Bir paytlar faqat boy odamlar:
- Shaxsiy yordamchiga ega edi
- Yozuvchini yollay olardi
- Dizaynerga ish bera olardi

Bugun — har kim. AI har bir odamga superkuch berdi.

Faqat ishlatish kerak.

Imkoniyat eshikni qoqyapti. Ochasizmi?""",
]


# ============================================
# ВЫБОР ТИПА ПОСТА
# ============================================

def get_video_series_post(post_index: int) -> str:
    """Возвращает пост серии AI-видеогенерации по индексу."""
    if 0 <= post_index < len(VIDEO_SERIES_POSTS):
        return VIDEO_SERIES_POSTS[post_index]
    return None


def get_daily_post(post_index: int) -> str:
    """Возвращает дневной пост по индексу."""
    return DAILY_AI_POSTS[post_index % len(DAILY_AI_POSTS)]


# ============================================
# ИНДЕКСЫ ДЛЯ ПОСЛЕДОВАТЕЛЬНОЙ ПУБЛИКАЦИИ
# ============================================

_video_post_index = 0
_daily_post_index = 0


# ============================================
# КАРТИНКА ЧЕРЕЗ UNSPLASH
# ============================================

IMAGE_QUERIES = {
    "video": ["video production", "camera cinema", "filmmaking", "ai technology"],
    "default": ["technology", "future", "innovation", "ai"],
}


def get_image_url(category: str = "default") -> str:
    queries = IMAGE_QUERIES.get(category, IMAGE_QUERIES["default"])
    query = random.choice(queries)
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
# ОБРЕЗКА ТЕКСТА ДО ЛИМИТА
# ============================================

def trim_text(text: str, max_length: int = 1024) -> str:
    """Обрезает текст до максимальной длины по предложениям."""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - 14]  # запас на "..."
    last_dot = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?'),
        truncated.rfind('\n\n')
    )
    
    if last_dot > 500:
        return truncated[:last_dot + 1]
    else:
        last_space = truncated.rfind(' ')
        return truncated[:last_space] + '.'


# ============================================
# ПУБЛИКАЦИЯ
# ============================================

async def publish_video_series_post():
    """Публикует пост серии AI-видеогенерации (13:00 и 19:00)."""
    global _video_post_index
    
    try:
        post_text = get_video_series_post(_video_post_index)
        
        if post_text is None:
            # Серия закончилась — публикуем дневной пост
            logger.info("📝 Серия AI-видео закончилась, публикуем дневной пост")
            post_text = get_daily_post(_daily_post_index)
        else:
            logger.info(f"📝 Серия AI-видео: пост {_video_post_index + 1}/{len(VIDEO_SERIES_POSTS)}")
            _video_post_index += 1
        
        cta = get_cta()
        hashtags = "\n\n" + get_hashtags()
        full_text = post_text + cta + hashtags
        full_text = trim_text(full_text, 1024)
        
        image_url = get_image_url("video")
        bot = Bot(token=BOT_TOKEN)
        
        if image_url:
            await bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=image_url,
                caption=full_text
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=full_text
            )
        
        logger.info(f"✅ Пост опубликован, длина: {len(full_text)}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации серии: {e}")


async def publish_morning():
    """13:00 Ташкент = 8:00 UTC."""
    await publish_video_series_post()


async def publish_evening():
    """19:00 Ташкент = 14:00 UTC."""
    await publish_video_series_post()


async def publish_greeting():
    """7:00 Ташкент = 2:00 UTC — Утреннее приветствие."""
    try:
        greeting = get_morning_greeting()
        hashtags = "\n\n" + get_hashtags()
        
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=greeting + hashtags
        )
        logger.info("✅ Утреннее приветствие опубликовано")
        
    except Exception as e:
        logger.error(f"❌ Ошибка приветствия: {e}")


async def publish_daily_ai_post():
    """17:00 Ташкент = 12:00 UTC — Дневной AI пост."""
    global _daily_post_index
    
    try:
        post_text = get_daily_post(_daily_post_index)
        _daily_post_index += 1
        
        cta = get_cta()
        hashtags = "\n\n" + get_hashtags()
        full_text = post_text + cta + hashtags
        full_text = trim_text(full_text, 1024)
        
        image_url = get_image_url("default")
        bot = Bot(token=BOT_TOKEN)
        
        if image_url:
            await bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=image_url,
                caption=full_text
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=full_text
            )
        
        logger.info(f"✅ Дневной AI пост опубликован (индекс {_daily_post_index})")
        
    except Exception as e:
        logger.error(f"❌ Ошибка дневного поста: {e}")


async def publish_poll():
    """Опросы — Пн/Ср/Пт в 20:00 Ташкент = 15:00 UTC."""
    try:
        poll = random.choice(POLLS)
        bot = Bot(token=BOT_TOKEN)
        await bot.send_poll(
            chat_id=CHANNEL_USERNAME,
            question=poll["question"],
            options=poll["options"],
            is_anonymous=True
        )
        logger.info("✅ Опрос опубликован")
        
    except Exception as e:
        logger.error(f"❌ Ошибка опроса: {e}")


async def keep_alive_ping():
    """Keep-alive каждые 10 минут."""
    try:
        tashkent_tz = timezone(timedelta(hours=5))
        now = datetime.now(tashkent_tz).strftime("%H:%M:%S")
        logger.info(f"💚 Keep-alive — Ташкент: {now}")
    except Exception as e:
        logger.error(f"Keep-alive error: {e}")


# ============================================
# MAIN
# ============================================

async def main():
    if PUBLISH_ON_STARTUP:
        logger.info("🧪 Тестовая публикация при запуске...")
        await publish_video_series_post()
    
    scheduler = AsyncIOScheduler(timezone="UTC")
    
    # 7:00 Ташкент = 2:00 UTC — Приветствие
    scheduler.add_job(
        publish_greeting,
        CronTrigger(hour=2, minute=0),
        id="greeting",
        replace_existing=True
    )
    
    # 13:00 Ташкент = 8:00 UTC — Утренний пост серии
    scheduler.add_job(
        publish_morning,
        CronTrigger(hour=8, minute=0),
        id="morning_post",
        replace_existing=True
    )
    
    # 17:00 Ташкент = 12:00 UTC — Дневной AI пост
    scheduler.add_job(
        publish_daily_ai_post,
        CronTrigger(hour=12, minute=0),
        id="daily_ai",
        replace_existing=True
    )
    
    # 19:00 Ташкент = 14:00 UTC — Вечерний пост серии
    scheduler.add_job(
        publish_evening,
        CronTrigger(hour=14, minute=0),
        id="evening_post",
        replace_existing=True
    )
    
    # Опросы Пн/Ср/Пт в 20:00 Ташкент = 15:00 UTC
    scheduler.add_job(
        publish_poll,
        CronTrigger(day_of_week="mon,wed,fri", hour=15, minute=0),
        id="poll",
        replace_existing=True
    )
    
    # Keep-alive каждые 10 минут
    scheduler.add_job(
        keep_alive_ping,
        IntervalTrigger(minutes=10),
        id="keep_alive",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Бот запущен v3.0")
    logger.info("📅 Расписание (Ташкент): 7:00 / 13:00 / 17:00 / 19:00")
    logger.info(f"🎬 Серия AI-видео: {len(VIDEO_SERIES_POSTS)} постов")
    logger.info(f"📰 Дневных постов: {len(DAILY_AI_POSTS)}")
    
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
