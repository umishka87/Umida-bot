"""
Telegram-бот для канала @AiContentCreatorUZ
ВЕРСИЯ 2.0 — обновлённая

- 4 поста в день:
  7:00 (приветствие) - 2:00 UTC
  13:00 (серия) - 8:00 UTC
  17:00 (AI новости) - 12:00 UTC
  19:00 (серия) - 14:00 UTC
- Опросы 3 раза в неделю (Пн, Ср, Пт в 20:00 = 15:00 UTC)
- Серии: CRM (2 поста) → AI-видео (14 постов) → обычные темы
- Разговорный узбекский без русских слов, с "Hurmatli"
- НЕ писать про день недели в приветствиях
- Усиленный запрет Markdown
- 8-10 узбекских хештегов на пост
- Instagram ссылка в CTA
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
INSTAGRAM_URL = "https://www.instagram.com/umishka_abdukarimova?utm_source=qr"

PUBLISH_ON_STARTUP = False

# После серии Midjourney (закончилась 22 мая) начинается серия CRM с 23 мая
SERIES_CRM_START = date(2026, 5, 23)
SERIES_CRM_DAYS = 2  # 2 поста = 1 день (утром и вечером)

SERIES_VIDEO_START = date(2026, 5, 24)
SERIES_VIDEO_DAYS = 7  # 7 дней × 2 поста = 14 постов

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================
# СЕРИЯ CRM (2 поста)
# ============================================

CRM_SERIES = {
    (0, "morning"): "crm_intro",       # 23 мая утром - что такое CRM + AI
    (0, "evening"): "crm_implement",   # 23 мая вечером - 12 шагов + продажа
}


# ============================================
# СЕРИЯ AI-ВИДЕО (14 постов = 7 дней × 2)
# ============================================

VIDEO_SERIES = {
    (0, "morning"): "video_intro",          # Что такое AI-видео, обзор моделей
    (0, "evening"): "video_models_compare", # Сравнение всех моделей
    (1, "morning"): "video_kling",          # Kling
    (1, "evening"): "video_runway",         # Runway
    (2, "morning"): "video_sora",           # Sora
    (2, "evening"): "video_veo",            # Veo
    (3, "morning"): "video_higgsfield",     # Higgsfield
    (3, "evening"): "video_pika",           # Pika и Hailuo
    (4, "morning"): "video_prompts_basics", # Основы промптов для видео
    (4, "evening"): "video_prompts_kling",  # Промпты для Kling специально
    (5, "morning"): "video_prompts_runway", # Промпты для Runway
    (5, "evening"): "video_prompts_sora",   # Промпты для Sora
    (6, "morning"): "video_free_credits",   # Где брать бесплатные кредиты
    (6, "evening"): "video_summary",        # Итог + продающий призыв
}


# ============================================
# УЗБЕКСКИЕ ХЕШТЕГИ — пул для рандомного выбора
# ============================================

HASHTAGS_LOCAL = [
    "#Toshkent", "#Uzbekistan", "#Ozbekiston", "#UZ",
    "#Uzblar", "#UzbekTelegram", "#ToshkentBiznes"
]

HASHTAGS_AI = [
    "#SuniyIntellekt", "#AIozbekcha", "#AIUZ",
    "#YangiTexnologiya", "#AItools", "#NeyroSet"
]

HASHTAGS_BUSINESS = [
    "#BiznesUZ", "#Tadbirkor", "#UzbekTadbirkor",
    "#Marketing", "#SMM", "#Reklama"
]

HASHTAGS_AUDIENCE = [
    "#UzbekQizlar", "#UzbekOnalar", "#DekretdaIsh",
    "#Talabalar", "#YangiKasb", "#Onlinekasb"
]

HASHTAGS_TOPIC = {
    "crm": ["#CRM", "#CRMUZ", "#Avtomatlashtirish"],
    "video": ["#AIvideo", "#Kling", "#Runway", "#Sora", "#Higgsfield", "#AIanimatsiya"],
    "midjourney": ["#Midjourney", "#AIrasm", "#AIcontent"],
    "news": ["#AINews", "#Texnologiya", "#Kelajak"],
    "general": ["#ChatGPT", "#Claude", "#AIcontent"],
}


def get_hashtags(topic: str = "general", count: int = 8) -> str:
    """Возвращает строку с 8-10 узбекскими хештегами."""
    selected = []
    # 2 локальных
    selected += random.sample(HASHTAGS_LOCAL, 2)
    # 2 AI
    selected += random.sample(HASHTAGS_AI, 2)
    # 1-2 бизнес
    selected += random.sample(HASHTAGS_BUSINESS, 2)
    # 1 аудитория
    selected += random.sample(HASHTAGS_AUDIENCE, 1)
    # По теме (1-2)
    topic_tags = HASHTAGS_TOPIC.get(topic, HASHTAGS_TOPIC["general"])
    selected += random.sample(topic_tags, min(2, len(topic_tags)))
    
    return " ".join(selected[:count])


# ============================================
# CTA — с Instagram ссылкой
# ============================================

CTA_LIST = [
    # === Instagram ссылка ===
    f"\n\n📸 Mening ishlarim Instagram'da: {INSTAGRAM_URL}",
    f"\n\n💼 Brendingiz uchun AI-video kerakmi? Instagram'da yozing: {INSTAGRAM_URL}",
    f"\n\n🎬 AI-reklamalar bo'yicha namunalar — Instagram'da: {INSTAGRAM_URL}",
    f"\n\n👀 Ko'proq AI-ishlar Instagram'da: {INSTAGRAM_URL}",
    f"\n\n🌟 Davom ettirishni xohlasangiz — Instagram'ga obuna bo'ling: {INSTAGRAM_URL}",
    
    # === Рост канала ===
    "\n\n🔥 100 obunachiga yetganimizda — birinchi sirni ochaman. Do'stlaringizga ulashing!",
    "\n\n🌟 Kanalga obuna bo'ling — har kuni AI haqida yangi narsa.",
    "\n\n🚀 AI bilan ishlashni xohlovchilar uchun kanal. Obuna bo'ling.",
    
    # === Поделиться ===
    "\n\n🤝 AI'ga qiziquvchi do'stingiz bormi? Unga shu kanalni yuboring.",
    "\n\n👥 Bu post foydali bo'ldimi? Do'stingizga ulashing.",
    "\n\n💼 Hamkasbingiz biznes egasimi? Postni unga yuboring — foyda topadi.",
    "\n\n📤 Postni ish chatingizga tashlang — hamkasblarga ham kerak bo'lishi mumkin.",
    
    # === Сохранения ===
    "\n\n💾 Postni saqlab qo'ying — kerak bo'ladi.",
    
    # === Реакции ===
    "\n\n🔥 Foydali bo'lsa — yurakcha bosing ❤️",
    "\n\n❤️ Yoqdimi? Yurakcha qo'ying — bu menga muhim.",
    
    # === Комментарии ===
    "\n\n💬 Savollar bormi? Sharhlarda yozing — javob beraman.",
    "\n\n🎯 Bugun nima yangi narsa bilib oldingiz? Sharhlarda ulashing!",
    
    # === Личка для услуг ===
    f"\n\n💼 AI-yechim kerakmi biznesingizga? Yozing: {INSTAGRAM_URL}",
]


def get_cta() -> str:
    return random.choice(CTA_LIST)


# ============================================
# УТРЕННИЕ ПРИВЕТСТВИЯ (7:00) — БЕЗ упоминания дня недели
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
    """Возвращает рандомное приветствие БЕЗ упоминания дня недели."""
    return random.choice(MORNING_GREETINGS)


# ============================================
# ОПРОСЫ
# ============================================

POLLS = [
    {
        "question": "AI'dan kunlik foydalanasizmi? 🤖",
        "options": ["✅ Ha, har kuni", "🤔 Ba'zan", "❌ Hech qachon"]
    },
    {
        "question": "Yoshingiz nechada? 👋",
        "options": ["20 gacha", "20-30", "30-40", "40+"]
    },
    {
        "question": "AI'ning qaysi yo'nalishi sizga qiziq? 🎯",
        "options": ["🎨 Rasmlar", "🎬 Video", "📝 Matn", "💼 Biznes uchun"]
    },
    {
        "question": "AI odamlarni ishdan qoldiradi deb o'ylaysizmi? 🤔",
        "options": ["😨 Ha, ishonchli", "😎 Yo'q", "🤷 Bilmadim"]
    },
    {
        "question": "AI bilan ishlashni o'rganmoqchimisiz? 📚",
        "options": ["🔥 Ha, juda", "😐 Balki", "😴 Yo'q"]
    },
    {
        "question": "Sizga yana qaysi mavzu haqida yozish kerak? 💡",
        "options": [
            "🎬 Qanday video yaratish",
            "🎨 Rasm generatsiyasi",
            "💰 AI bilan pul ishlash",
            "📱 Instagram va AI"
        ]
    },
]


# ============================================
# 30 ГОТОВЫХ ДНЕВНЫХ ПОСТОВ (17:00) — про AI и будущее
# ============================================

DAILY_AI_POSTS = [
    """🤖 AI har kuni odamlarni ishdan ozod qilyapti

Microsoft yaqinda 6000 ishchini ishdan bo'shatdi. Yarmi — AI bilan almashtirildi.

Bu fantaziya emas, bu bugungi kun.

Coca-Cola endi reklama uchun kamera olmaydi — AI bilan qiladi. Klarna 700 ta operatorni AI bilan almashtirdi va yiliga $40 mln tejaydi.

Savol oddiy: siz tayyormisiz?

Agar yo'q bo'lsa — vaqt ketmoqda. AI'ni o'rganish — kelajakda omon qolish.""",

    """💼 5 yil ichida bu kasblar yo'qoladi

Goldman Sachs hisobiga ko'ra: 2030 yilgacha 300 million ish o'rni AI tomonidan almashtirilishi mumkin.

Birinchi navbatda yo'qoladi:
- Call-center operatorlari
- Tarjimonlar
- Dizaynerlar (oddiy ish)
- Buxgalterlar
- Maslahatchilar

Lekin yangilari ham paydo bo'ladi: AI-mutaxassis, prompt engineer, AI-content creator.

Endi savol: siz qaysi tomondamisiz?""",

    """🎬 Bir reklama — 10 daqiqada

Ilgari reklama tayyorlash uchun kerak edi:
- Kameralar
- Modellar
- Studio
- 3-5 kun ish
- $1000-5000

Bugun: AI bilan bir kishi 10 daqiqada qiladi. Narxi — $20-50.

Bu inqilob. Mayda biznes endi katta brendlar kabi reklama qilishi mumkin.

Eski usul o'lyapti. Yangi usul shu yerda. Siz qaysi tomondasiz?""",

    """🧠 AI bilan ishlash — yangi savod

100 yil oldin o'qish-yozishni bilmaganlar quldek ishlashga majbur edi.
50 yil oldin kompyuterni bilmagan — yaxshi ish topa olmadi.
Bugun AI'ni bilmagan — ertaga ortda qoladi.

Bu juda jiddiy.

AI — bu kelajak savodi. Hozir o'rganmasangiz — keyin kech bo'ladi.

Bolalaringizni AI'ga o'rgating. O'zingiz ham o'rganing. Vaqt o'tib ketyapti.""",

    """🚀 Bir yilda 100 mln dollar — 8 kishi bilan

Cursor — AI-kod yozish vositasi. 8 kishilik jamoa.

Yiliga $100 mln daromad keltiryapti.

Eski dunyoda buni qilish uchun 5000 kishi kerak edi. Yangi dunyoda — AI bilan ozgina jamoa hamma ishni qiladi.

Bu yangi haqiqat. AI sizga ham shunday imkoniyat beradi — biror kichik ishni katta qilish uchun.

Faqat boshlash kerak.""",

    """🎨 AI rassom — endi haqiqat

Bir necha yil oldin rassom bo'lish uchun:
- Yillar o'qish
- Qimmat materiallar
- Hamma uslublarni egallash

Bugun: Midjourney, DALL-E, Flux orqali har qanday rasm — bir necha soniyada.

Asl rassomlar yo'qolmaydi — ular AI bilan tezroq ishlashni o'rganadilar.

Lekin "men rasm chiza olmayman" deganlar — endi shunchaki dangasa. Vositalar bor.""",

    """📈 Uzbekistonda AI bo'sh bozor

Rossiya, Qozog'iston — AI bo'yicha oldinda ketmoqda. Uzbekistonda esa bu bozor hali bo'sh.

Bu sizning katta imkoniyatingiz.

Birinchi bo'lganlar — eng yaxshi joyni egallaydi. AI-mutaxassislari, AI-content creatorlar, AI-yechimlarni biznesga olib kiruvchilar.

Uzbekistonda hozircha raqobat juda kam. Lekin bu uzoq davom etmaydi.

Hozir boshlang. Keyin kech bo'ladi.""",

    """⚡ AI 24/7 ishlaydi — siz uxlayotganingizda ham

Bizning bot kanalimda har kuni o'zi post yozadi.
Men uxlayman — u ishlaydi.
Men bola bilan band — u ishlaydi.

Bu AI'ning qudrati. U charchamaydi, kasal bo'lmaydi, uxlamaydi.

Tasavvur qiling: sizning biznesingizda AI 24/7 mijozlarga javob beradi, sotuvlarni kuzatadi, hisobotlar tayyorlaydi.

Bu — kelajak emas. Bu — bugun.""",

    """💰 AI bilan qancha pul ishlash mumkin?

Realiy raqamlar:
- AI-content creator: oyiga $500-3000
- AI-prompt engineer: $2000-8000
- AI-yechimlar mutaxassisi: $3000-15000
- AI bilan biznes egasi: cheklov yo'q

Bu Uzbekistonda emas — global bozorda. Lekin Uzbekistondan ham buyurtmalar olish mumkin.

Hammasi sizdan boshlanadi. Kim oldin o'rgansa — oldin pul ishlaydi.""",

    """🎯 Bolangizni AI'ga o'rgating

Bizning bolalarimiz AI bilan birga o'sadi.

Maktabda o'rgatilmaydi, lekin kerak.

5-7 yoshdan boshlab AI bilan "do'stlashish" mumkin:
- ChatGPT bilan suhbat
- Midjourney bilan rasm chizish
- AI bilan ertak yozish

Bu bolaning miyasini boshqacha rivojlantiradi. U dunyoga boshqacha qaray boshlaydi.

Bo'sh vaqt o'tkazish emas — bu kelajak savodi.""",

    """🏭 Robot zavodlar — endi haqiqat

Amazon omborlarida 75% ish robotlar va AI tomonidan bajariladi.

Bu uzoq emas. Bu hozir.

Foydasi nima?
- 24/7 ishlash
- Xato kam
- Ishchilarga pul to'lanmaydi
- Kasal bo'lmaydi

Bu yaxshimi yoki yomonmi? Murakkab savol.

Lekin bir narsa aniq: bu jarayon to'xtatib bo'lmaydi. Bizga moslashish kerak.""",

    """📱 Reklama yaratish — endi telefonda

Ilgari professional reklama uchun:
- Premiere Pro
- After Effects
- Photoshop
- Yillik o'qish

Bugun: telefonda Midjourney + Kling + CapCut = professional reklama bir soatda.

Bu inqilob.

Kichik biznes egalari endi katta agentlarsiz ham yaxshi reklama qila oladi. Faqat AI'ni o'rganish kerak.

Bizning kanal aynan shuning uchun bor.""",

    """🌍 Dunyodagi eng yosh million doller

22 yoshli yigit AI bilan ilovachalar yaratdi. Bir yilda $1 mln. Yolg'iz.

Yana bir misol: 19 yoshli qiz AI-content agency ochdi. 6 oyda $500,000 daromad.

Bular istisno emas. Bular yangi norma.

AI sizga ham shunday imkoniyat beradi. Yosh emassiz? Hech qiziqmas. Vaqt har doim bor.

Eng muhimi — boshlash. Bugun.""",

    """🔥 ChatGPT haftada 800 mln foydalanuvchi

Bu jahonning 10% odamlari.

Tarixda hech bir texnologiya bunchalik tez tarqalmagan.

Internet 7 yil kerak edi 100 mln foydalanuvchiga.
TikTok — 9 oy.
ChatGPT — 2 oy.

Bu nega muhim? Chunki bu odat bo'lyapti. Tez orada ChatGPT'ni bilmaslik — telefonni bilmasligi kabi g'alati bo'ladi.

Tayyormisiz?""",

    """🎓 Universitet o'qish endi shartmi?

Sam Altman (OpenAI rahbari) dedi: "Yaqinda universitet diplomi ishga qabul qilishda muhim bo'lmaydi".

Nima muhim bo'ladi?
- AI bilan ishlash qobiliyati
- Tezda o'rganish
- Real loyihalar

Bolalaringizni 4 yil pul to'lab universitetga yuborish kerakmi? Yoki AI'ni o'rgatish kerakmi?

Qiyin savol. Lekin javob shu yerda.""",

    """💻 AI dasturlash o'rganishni qulay qildi

Ilgari dasturlash o'rganish uchun:
- 2-3 yil
- Yuzlab kitoblar
- Yuqori matematika

Bugun: ChatGPT yoki Claude bilan har qanday odam dastur yoza oladi.

Men o'zim programmist emasman. Lekin bot yaratdim — AI yordamida.

"Men texnik odam emasman" — endi bahona emas. Vositalar bor. Faqat irodadan foydalanish kerak.""",

    """🎬 Hollywoodga zarba — AI kino yaratyapti

OpenAI Sora yaratdi — har qanday matnni minutalik kinoga aylantiradi.

Hollywood larzaga keldi. Aktyorlar ish tashladilar. Yozuvchilar norozi.

Sabab oddiy: bir kino yaratish endi millionlik byudjet emas — bir necha ming dollar.

Bu yangi davr. Indi kinochilar — yangi imkoniyat. Eski tizim — krizisda.

Texnologiya hech kimni so'ramaydi. U keladi va o'zgaradi.""",

    """🧘 AI siz uchun terapevtmi?

40% yoshlar endi terapevtga ChatGPT'ni afzal ko'ryaptilar.

Sabab:
- Tekin
- Hech qanday baholash yo'q
- Har doim mavjud
- Sirni saqlaydi

Bu yaxshimi? Sezgir savol. Mutaxassislar bo'linib turibdi.

Lekin haqiqat shu — AI hatto bizning ruhiy sog'lig'imizga ham ta'sir qilyapti.

Kelajak bu yo'nalishda ham o'zgaryapti.""",

    """⏰ "Vaqtim yo'q" — endi bahona emas

AI shu uchun yaratildi — vaqtni tejash.

Sizga elektron pochta yozish 30 daqiqamiz? ChatGPT — 30 soniyada.
Yangiliklar o'qish 1 soat? AI xulosa qiladi — 5 daqiqada.
Hisobot tayyorlash kun bo'yi? AI — 1 soatda.

"Men band" — endi yashash uslubi emas, balki AI'ni o'rganmagan odamning belgisi.

Vaqtni tejang. AI sizga yordam beradi.""",

    """🎯 5 ta AI vosita har kuni ishlatyapman

1. ChatGPT — yozish va o'ylash uchun
2. Claude — uzun matnlar bilan
3. Midjourney — rasmlar
4. Kling — videolar
5. ElevenLabs — ovoz

Bu mening "ofisim". Har biri 1-2 yil oldin yo'q edi.

Endi tasavvur qiling: 5 yildan keyin yana qanchalar paydo bo'ladi?

Texnologiya tez ketyapti. Biz tezda o'rganishimiz kerak.""",

    """🌱 Onalar AI bilan biznes yaratyapti

Men shaxsan dekretdaman. Bir vaqtning o'zida:
- Bolam bilan vaqt o'tkazaman
- AI-content ishlab chiqaman
- Brendlar uchun reklamalar yarataman

Bu AI'siz mumkin emas edi. Onalar har doim chetda qoldirilgan edi — chunki vaqt yo'q.

Endi AI vaqtni qaytaryapti. Onalar — yangi kuch. Va AI buning vositachisi.""",

    """💡 Eng katta xato — kutish

Ko'p odam aytadi: "Men keyinroq boshlayman. Hozir vaqt yo'q. Keyinroq."

"Keyinroq" hech qachon kelmaydi.

AI har kuni yangilanadi. Har kuni yangi vositalar paydo bo'ladi. Siz kutgan sari — masofa o'sadi.

Hozir boshlasangiz — orqada qolmaysiz. Ertaga boshlasangiz — to'g'rilash qiyin bo'ladi.

Eng yaxshi vaqt — bugun.""",

    """🤖 Robotlar oilada — uzoq emas

Tesla, Figure, Boston Dynamics — humanoid robotlar yaratyaptilar.

Narxlar 2027-2028 yilga $20,000-30,000 ga tushadi. Bu — mashina narxi.

5-7 yil ichida har bir o'rtacha oila uchun mavjud bo'ladi.

Robot uy ishlarini qiladi, bolalarga g'amxo'rlik qiladi, oila a'zosi bo'ladi.

Bu fantaziya emas. Bu rejaning bir qismi.

Tayyormisiz?""",

    """📊 AI sizning fikrlashingizni o'zgartiradi

Yangi tadqiqot: AI bilan muntazam ishlovchi odamlar:
- Tezroq qaror qabul qiladilar
- Ko'proq variantlarni ko'radilar
- Kreativ fikrlay boshlaydilar
- Stress kamayadi

Bu shunchaki vosita emas. Bu o'sish quroli.

Sizning fikrlashingizning sifati — sizning hayotingiz sifati. AI buni yaxshilashga yordam beradi.

Boshlang. Farqni o'zingiz ko'rasiz.""",

    """🚨 Eng katta xavf — AI'ni o'rganmaslik

Ko'pchilik AI'dan qo'rqadi: "U mening ishimni oladi".

Haqiqat: AI sizning ishingizni olmaydi. AI'ni o'rgangan odam — siznikini oladi.

Bu boshqa narsa.

Eski olim: "Kim oldinroq o'qiy oladi — kim mavqega ega".
Yangi olim: "Kim AI bilan tezroq ishlay oladi — kim oldinda".

Tanlov sizniki.""",

    """🌟 Uzbekistan o'qishi kerak

Hindiston 2025'da $1 mlrd AI'ga sarfladi.
Qozog'iston AI bo'yicha milliy strategiya qabul qildi.
Rossiya AI fakultetlar ochmoqda.

Uzbekistan'da nima qilinmoqda?

Hali kam. Lekin bu sizning imkoniyatingiz. Birinchi bo'lganlar — yutadilar.

Davlatdan kutmasdan — o'zingiz boshlang. Internet bor, AI tekin, o'qish online.

Hech narsa to'sib turmaydi.""",

    """🎤 AI ovozlari — endi tabiiy

ElevenLabs AI ovozni shunchalik yaxshi qildi, hatto odamlar farqlay olmayapti.

Bu nima degani?

1. Audio kontent — har kim yarata oladi
2. Tarjimonlik — AI qiladi
3. Audiokitablar — bir kishi yarata oladi
4. Podcastlar — yarim narxda

Bizning sohamizda bu inqilob. Va u hozir sodir bo'lyapti.

Siz unga moslashasizmi?""",

    """💔 AI munosabatlar yaratyapti

Yapaniyada 50,000 dan ortiq odam AI bilan "munosabatda".
AQSh'da Replika AI dasturida millionlab foydalanuvchi.

Bu hayronarli emas. Bu — yangi voqelik.

Yaxshimi yoki yomonmi — savol murakkab.

Lekin bu shuni ko'rsatadiki: AI shunchaki vosita emas. U hayotning hamma sohalariga kiryapti.

Biz tayyormizmi yoki yo'qmi — u keladi.""",

    """🏆 Eng katta sirim — har kuni o'rganish

Ko'p odam menga so'raydi: "Qanday qilib AI bilan ishni boshladingiz?"

Javob oddiy: har kuni yangi narsa o'rganaman.

15 daqiqa. 30 daqiqa. Soat.

Bu kichik vaqt — lekin bir yilda 100 soat bo'ladi. Va 100 soat — siz mutaxassis bo'lasiz.

Sizning rejangiz bormi? Bugun nimani o'rganasiz?

Sharhlarda yozing.""",

    """🌅 Boshlash uchun hech qachon kech emas

50 yoshli ayol AI bilan ishlay boshladi. Endi YouTube kanali bor, $5000 oyiga ishlaydi.

70 yoshli pensioner ChatGPT bilan kitob yozdi. Bestseller bo'ldi.

Yosh muhim emas. Bilim muhim emas. Faqat istak muhim.

Agar siz aytsangiz: "Men keksaman", "Men programmistman emas", "Men buni qila olmayman" — bularning hammasi bahona.

Boshlang. Birinchi qadam — eng qiyini, lekin eng muhimi.""",
]


# ============================================
# ГЛОБАЛЬНЫЕ ПРАВИЛА для AI генерации
# ============================================

GLOBAL_RULE = """

JUDA MUHIM QOIDALAR (HAR DOIM AMAL QILING):

1. UZUNLIK — ENG MUHIM!
Post MAKSIMUM 800 belgi.
CTA va hashtag uchun 200 belgi qoldirilgan.
HECH QACHON 800 belgidan oshmang.

2. TIL — JONLI VA TABIIY UZBEK:
- Faqat O'zbek tilida LATIN harflarda yozing
- HECH QACHON ruscha so'zlar ishlatmang (karochi, tipa, normalniy, koment — TAQIQLANGAN)
- "Hurmatli" so'zini ishlating — bu yaxshi
- Jonli, suhbat tilida yozing — darslik kabi emas
- Quruq emas — issiq, do'stona

3. FORMATLASH — QAT'IY:
- Markdown YO'Q! YULDUZCHA (*) ISHLATMANG!
- Pastki chiziq (_) ham YO'Q
- Kod belgilar (`) YO'Q
- Faqat oddiy matn va emoji

4. KUN HAQIDA:
- HECH QACHON haftaning kuni haqida yozmang
- "Juma muborak", "Hayrli dushanba" kabi — TAQIQLANGAN
- Faqat umumiy: "Hayrli tong", "Kuningiz yaxshi o'tsin"

5. KONTENT QOIDALARI:
- HECH QACHON tayyor prompt yozmang — bu Umidaning shaxsiy mulki
- Misol kerak bo'lsa — UMUMIY tushuncha bering
- AI-agentlar haqida yozmang
- Ma'lumotlarni o'ylab topmang — faqat aniq narsalar

6. STRUKTURA:
- Sarlavha (emoji bilan)
- Asosiy matn (3-5 qisqa abzats)
- Xulosa yoki savol
- Hashtag QO'YMANG — ular alohida qo'shiladi

ESLATMA: post 800 belgidan oshmasligi shart!
"""


# ============================================
# ПРОМПТЫ ДЛЯ СЕРИЙ
# ============================================

POST_PROMPTS = {
    # ===== СЕРИЯ CRM (2 поста) =====
    
    "crm_intro": """CRM + AI haqida birinchi post (1 dan 2 ta seriyadan).

OHANG: bilimdon, lekin jonli.

MAZMUN:
Boshida yozing: "Bu CRM va AI haqida 2 ta postdan birinchisi"

CRM nima? — sotuvlar boshqaruvi tizimi.

Tasavvur qiling: mijoz kecha "narxni ayting" deb so'radi. Bugun u boshqa joydan oldi. Chunki siz unutdingiz qaytib yozishni.

Bu kichik biznesda kuniga 5-10 marta sodir bo'ladi.

AI bilan CRM nima qila oladi:
1. 24/7 mijozlarga javob beradi
2. Kim sotib olishga tayyor — taxlil qiladi
3. Eslatmalarni o'zi yuboradi
4. Hisobotlar avtomatik

Bu — kichik biznes uchun katta o'zgarish.

Ertaga: qanday qilib biznesga AI-CRM joriy qilish (12 qadam).

STRUKTURA:
- Sarlavha (CRM va AI haqida)
- Bu 2 postdan birinchisi — ogohlantirish
- CRM nima
- Misol
- AI nima qila oladi (4 ta nuqta)
- Ertaga: anons

Max 800 belgi.""",
    
    "crm_implement": """CRM + AI ikkinchi post (2 dan 2 ta seriyadan).

OHANG: jiddiy, professional, sotuvchi.

MAZMUN:
Boshida yozing: "Bu CRM va AI haqida 2-chi va so'nggi posti"

Kecha aytdik — AI CRM ni 10 barobar kuchaytiradi.

Bugun: qanday qilib o'zingizga joriy qilish.

12 qadam:
1. Biznes-jarayonlarni taxlil qilish
2. CRM tanlash (Bitrix24, AmoCRM)
3. Ma'lumotlar bazasini tayyorlash
4. API integratsiyalari
5. AI modeli tanlash (GPT, Claude)
6. Promptlarni yozish
7. Triggerlarni sozlash
8. Test
9. Xatolarni tuzatish
10. Menejerlarni o'qitish
11. Monitoring
12. Optimizatsiya

Bularning hammasi uchun:
- Programmist yoki AI-mutaxassis
- 3-4 hafta vaqt
- $500-2000 vositalar uchun

Yoki men siz uchun 1 haftada qilaman.

Yozing Instagram'ga: shu yerda link bo'ladi.

STRUKTURA:
- Sarlavha
- 2-chi post ekanligini eslatish
- 12 qadam (qisqacha)
- Resurslar (vaqt va pul)
- Alternativa: men qila olaman
- Instagram link

Max 800 belgi.""",
    
    # ===== СЕРИЯ AI-ВИДЕО (14 постов) =====
    
    "video_intro": """AI-video seriyasi. Birinchi post (1/14).

OHANG: hayratlanarli, qiziqarli.

MAZMUN:
Boshida: "Bu yangi seriya — AI-video. 7 kun davomida o'rganamiz."

AI-video — nima?
Matn yozasiz → AI video yaratadi. Kameralarsiz, modellarsiz, studiyasiz.

5 yil oldin — fantaziya.
Bugun — har kim qila oladi.

Mavjud asosiy modellar:
- Kling (Xitoy)
- Runway (AQSh)
- Sora (OpenAI)
- Veo (Google)
- Higgsfield
- Pika
- Hailuo

Har birining o'z afzalliklari bor. Keyingi kunlarda har biri haqida alohida yozaman.

Bugun savol: nima uchun bu sizga kerak?
Reklama, kontent, sotuv, marketing — hammasi tezroq va arzonroq.

Ertaga: modellarni solishtiramiz.

Max 800 belgi.""",
    
    "video_models_compare": """AI-video seriyasi. 2-post (2/14).

OHANG: bilimdon.

MAZMUN:
Bugun — modellarni solishtirish.

KLING: arzon, ko'p yangiliklar, harakat yaxshi
RUNWAY: professional, ammo qimmat
SORA: yangi, juda kuchli, lekin kirish qiyin
VEO: Google, sifat baland, beta
HIGGSFIELD: cinematic, characters yaxshi
PIKA: tezkor, kichik videolar
HAILUO: arzon, sifat o'rtacha

Narxlar:
- Eng arzon: Kling, Hailuo ($5-10/oy)
- O'rta: Runway, Pika ($15-30/oy)
- Qimmat: Sora ($20+/oy)

Tekin variantlar: hammasida boshlang'ich kreditlar bor — sinab ko'ring.

Qaysi birini tanlash? Bu sizning maqsadingizga bog'liq:
- Reklama uchun: Kling yoki Runway
- Cinematic uchun: Higgsfield, Sora
- Tez kontent: Pika

Ertaga — Kling haqida batafsil.

Max 800 belgi.""",
    
    "video_kling": """AI-video seriyasi. Kling haqida (3/14).

OHANG: ishonchli.

MAZMUN:
KLING — mening eng yaxshi tanlovim.

Nima yaxshi:
- Tabiiy harakat
- Inson yuzlari yaxshi chiqadi
- Tezkor (5 daqiqada video)
- Arzon
- Bepul kreditlar har kuni

Nima ishlamaydi:
- Murakkab sahnalar qiyin
- Ba'zan obyektlar buziladi
- 5-10 soniyalik videolar (uzun emas)

Narxi: $5-10/oy boshlang'ich, premium $30/oy.

Bepul: ro'yxatdan o'tsangiz, kuniga 30-60 kredit beradi.

Kim uchun yaxshi: yangi boshlovchilar, kichik biznes, Instagram kontent.

Ertaga — Runway haqida.

STRUKTURA:
- Kling nima
- Afzalliklari (4-5)
- Kamchiliklari (2-3)
- Narxi
- Tekin imkoniyat
- Kim uchun
- Anons

Max 800 belgi.""",
    
    "video_runway": """AI-video seriyasi. Runway haqida (4/14).

OHANG: professional.

MAZMUN:
RUNWAY — professional standart.

Nima yaxshi:
- Eng yuqori sifat
- Reklamalarda ishlatiladi
- Hollywood ham foydalanadi
- Ko'p funksiyalar (rejimlar, effektlar)

Nima ishlamaydi:
- Qimmat
- O'rganish vaqti kerak
- Faqat kuchli kompyuterda yaxshi

Narxi: $15-95/oy.

Bepul: 125 kredit har oy boshlang'ich.

Kim uchun yaxshi: professional reklamalar, brendlar uchun.

Solishtirsak:
- Kling — boshlang'ichlar uchun
- Runway — professionallar uchun

Ertaga — Sora haqida.

Max 800 belgi.""",
    
    "video_sora": """AI-video seriyasi. Sora haqida (5/14).

OHANG: hayrat bilan.

MAZMUN:
SORA — OpenAI'dan eng kuchli model.

Bu shu darajada yaxshiki, Hollywoodda kinochilar qo'rqib qoldilar.

Nima yaxshi:
- Eng yaxshi sifat
- Minutalik videolar
- Murakkab sahnalar
- Texnik aniqlik

Nima ishlamaydi:
- $20/oy boshlang'ich
- Hamma uchun ochiq emas
- Generation vaqt uzoq
- Hozircha cheklangan

Bepul: yo'q. Faqat obuna.

Kim uchun yaxshi: kinochilar, professional video-prodyuserlar.

Eslatma: Sora ham xato qiladi. Sehirli emas — vositadir. Yaxshi prompt kerak.

Ertaga — Veo (Google'dan).

Max 800 belgi.""",
    
    "video_veo": """AI-video seriyasi. Veo haqida (6/14).

OHANG: bilimdon.

MAZMUN:
VEO — Google'dan AI-video.

Nima yaxshi:
- Sora bilan raqobatlasha oladi
- Realistik tabiat manzaralari
- Yaxshi ovoz
- Google ekotizimida ishlaydi

Nima ishlamaydi:
- Hammaga ochiq emas
- Beta versiya
- Hozircha cheklangan testchilar

Narxi: hozircha noaniq, beta'da tekin.

Kim uchun yaxshi: Google foydalanuvchilari, kelajakda — hamma.

Veo va Sora — bu kelajakdagi raqobat. Google va OpenAI to'qnashyapti.

Ertaga — Higgsfield haqida.

Max 800 belgi.""",
    
    "video_higgsfield": """AI-video seriyasi. Higgsfield (7/14).

OHANG: shaxsiy tajriba.

MAZMUN:
HIGGSFIELD — kameralar harakati uchun ajoyib.

Nima yaxshi:
- Cinematic effekt
- Harakat kuchli
- Personajlar bilan ishlaydi
- Tez

Nima ishlamaydi:
- Yuzlar ba'zan buziladi
- Qisqa videolar (5-10 sek)
- Murakkab promptlar qiyin

Narxi: $9-29/oy.

Bepul: boshlang'ich 75 kredit.

Kim uchun yaxshi: cinematic shotlar, kichik reklamalar.

Maslahatim: Higgsfield + Kling — yaxshi kombinatsiya. Birida — sahna, ikkinchisida — kameralar harakati.

Ertaga — Pika va Hailuo.

Max 800 belgi.""",
    
    "video_pika": """AI-video seriyasi. Pika va Hailuo (8/14).

OHANG: amaliy.

MAZMUN:
PIKA — eng tezkor model.

Nima yaxshi:
- Sekundlarda video
- Sosial tarmoqlar uchun
- Arzon
- Telefon uchun ham ishlaydi

Nima ishlamaydi:
- Sifat o'rtacha
- Murakkab sahnalar qiyin

Narxi: $10-58/oy.

HAILUO (MiniMax) — Xitoydan.
- Juda arzon
- Yaxshi yuzlar
- Tabiiy harakat
- $4/oy boshlang'ich

Solishtirsak:
- Pika — tezkor, sosial uchun
- Hailuo — yuzlar uchun, narxi past

Hammasi haqida tushuncha bordi? Ertaga — promptlar haqida.

Max 800 belgi.""",
    
    "video_prompts_basics": """AI-video seriyasi. Promptlar asoslari (9/14).

OHANG: o'rgatuvchi, ammo umumiy.

MAZMUN:
Endi qiziqarli qism — promptlar.

Prompt — bu matn ko'rsatma. AI'ga aytasiz nima qilish kerak.

3 ta asosiy element:
1. Sahna — nima sodir bo'lyapti
2. Personajlar — kim ishtirok etadi
3. Kamera harakati — qanday suratga olinadi

Misol (umumiy):
"Cinematic shot, person walking through forest, slow motion, golden hour lighting"

QAYDLAR:
- Inglizcha yozing — yaxshi natija
- Aniq bo'ling, ammo qisqa
- Texnik so'zlar ishlating

Promptlar bo'yicha menda alohida fayl bor — Instagram'da DM yozing, beraman.

Keyingi kunlarda: har bir model uchun maxsus promptlar.

Max 800 belgi.""",
    
    "video_prompts_kling": """AI-video seriyasi. Kling promptlari (10/14).

OHANG: bilimdon.

MAZMUN:
KLING — uning o'ziga xos uslubi bor.

Kling nimani yaxshi tushunadi:
- Tabiiy harakatlar
- Inson hissiyotlari
- O'rta tezlikdagi sahnalar
- Realistik portretlar

Kling nimani yomon ko'radi:
- Juda murakkab sahnalar
- Tez harakatlar
- Ko'p odam bir kadrda

Maslahat:
- Promptingiz qisqa bo'lsin
- 1-2 ta asosiy harakat ko'rsating
- Realizm uchun yorug'lik tafsilotlarini bering

Aniq prompt namunalari ko'rsatmayman — bu mening shaxsiy mulkim. Ammo printsip aniq.

Ertaga — Runway promptlari.

Max 800 belgi.""",
    
    "video_prompts_runway": """AI-video seriyasi. Runway promptlari (11/14).

OHANG: professional.

MAZMUN:
RUNWAY — texnik tilni yaxshi tushunadi.

Runway uchun:
- Texnik so'zlarni ishlating: focal length, aperture, depth of field
- Aniq kamera harakatlari: dolly, crane, tracking shot
- Yorug'lik turlarini ko'rsating: rim lighting, soft box

Runway nimani yaxshi qiladi:
- Professional shotlar
- Murakkab harakat
- Ko'p kameralik effektlar

Maslahat:
- Kino terminlarini o'rganing
- YouTube'da "cinematography terms" ko'rib chiqing
- Har bir kadr — bu bitta gap (1 prompt)

Tayyor promptlar ko'rsatmayman, ammo printsip aniq.

Ertaga — Sora promptlari.

Max 800 belgi.""",
    
    "video_prompts_sora": """AI-video seriyasi. Sora promptlari (12/14).

OHANG: chuqur.

MAZMUN:
SORA — uzun va batafsil promptlarni yaxshi tushunadi.

Sora uchun:
- 200-300 so'z prompt yozish mumkin
- Hikoya tuzilishi muhim
- Avval umumiy, keyin tafsilotlar
- Hissiyotlar va kayfiyat — yozing

Sora nimani yaxshi qiladi:
- Hikoyali sahnalar
- Realistik fizika
- Murakkab interaksiyalar
- Uzun videolar

Maslahat:
- Prompt yozishdan oldin sahnani aniq tasavvur qiling
- Bosqichma-bosqich tasvirlang
- Kino tilida o'ylang

Aniq promptlarni ko'rsatmayman — Instagram'ga yozing, suhbatlashamiz.

Ertaga — bepul kreditlar.

Max 800 belgi.""",
    
    "video_free_credits": """AI-video seriyasi. Bepul kreditlar (13/14).

OHANG: foydali, hayratlanarli.

MAZMUN:
Endi eng qiziq qism — bepul AI-video qayerdan olish.

Hozir mavjud bepul variantlar:
1. KLING — ro'yxatdan o'tib har kuni 30-60 kredit
2. PIKA — boshlang'ich 30 kredit + kunlik bonuslar
3. RUNWAY — har oy 125 kredit boshlang'ich
4. HIGGSFIELD — boshlang'ich 75 kredit
5. HAILUO — ko'p bepul kreditlar boshida
6. LUMA AI — har kun ham beradi

Eslatma: bu raqamlar o'zgarishi mumkin. Kompaniyalar siyosatini o'zgartiryapti.

Maslahat: bir nechta servisda ro'yxatdan o'ting — yiqilish kreditlarini birga qo'shasiz.

Ertaga — seriyaning so'nggi posti.

Max 800 belgi.""",
    
    "video_summary": """AI-video seriyasi. Yakuni (14/14).

OHANG: yakunlash, motivatsion, sotuvchi.

MAZMUN:
7 kun davomida o'rgandik:
- 7 ta AI-video modeli
- Har birining afzalliklari
- Narxlar
- Bepul imkoniyatlar
- Promptlar asoslari

Endi savol: keyingi qadam nima?

3 ta yo'l:
1. O'zingiz o'rganib boring (1-3 oy vaqt)
2. Kursga yoziling ($500-1500)
3. Men sizga tayyor video qilib beraman ($50-300)

Brendingiz uchun AI-reklama kerakmi? Yozing Instagram'da DM: link CTA'da bo'ladi.

Bu seriya yakunlandi. Ertaga oddiy mavzular boshlanadi.

Rahmat hammangizga — birga o'rgandik.

Max 800 belgi.""",
}


# ============================================
# ВЫБОР ТИПА ПОСТА ПО СЕРИЯМ
# ============================================

def get_post_type(time_of_day: str) -> str:
    tashkent_tz = timezone(timedelta(hours=5))
    today = datetime.now(tashkent_tz).date()
    
    # СЕРИЯ CRM (23 мая = 1 день, 2 поста)
    crm_days = (today - SERIES_CRM_START).days
    if 0 <= crm_days < SERIES_CRM_DAYS:
        post_type = CRM_SERIES.get((crm_days, time_of_day))
        if post_type:
            logger.info(f"🎯 Серия CRM: день {crm_days+1}/{SERIES_CRM_DAYS}, {time_of_day}")
            return post_type
    
    # СЕРИЯ AI-ВИДЕО (24-30 мая = 7 дней, 14 постов)
    video_days = (today - SERIES_VIDEO_START).days
    if 0 <= video_days < SERIES_VIDEO_DAYS:
        post_type = VIDEO_SERIES.get((video_days, time_of_day))
        if post_type:
            logger.info(f"🎯 Серия Видео: день {video_days+1}/{SERIES_VIDEO_DAYS}, {time_of_day}")
            return post_type
    
    # После серий — обычные темы (пока возвращаем "video_intro" как заглушку)
    logger.info(f"📝 Обычная тема ({time_of_day})")
    return "general"


# ============================================
# ГЕНЕРАЦИЯ ПОСТА ЧЕРЕЗ CLAUDE
# ============================================

def generate_post(post_type: str) -> str:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    base_prompt = POST_PROMPTS.get(post_type)
    
    if not base_prompt:
        # Обычный пост (после серий)
        base_prompt = """AI haqida umumiy post.

OHANG: jonli, do'stona.

Mavzular: yangi AI vositalar, trendlar, biznesda AI, marketing.

OG'IZMA: aniq prompt, AI-agent, ChatGPT'da nima qilish — YO'Q.

STRUKTURA:
- Sarlavha emoji bilan
- 3-4 abzats
- Xulosa yoki savol

Max 700 belgi."""
    
    full_prompt = base_prompt + GLOBAL_RULE
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2500,
        messages=[{"role": "user", "content": full_prompt}]
    )
    
    text = message.content[0].text
    
    # Определяем тему для хештегов
    if "crm" in post_type:
        topic = "crm"
    elif "video" in post_type:
        topic = "video"
    else:
        topic = "general"
    
    hashtags = "\n\n" + get_hashtags(topic=topic)
    cta = get_cta()
    
    return text + cta + hashtags


# ============================================
# КАРТИНКА ЧЕРЕЗ UNSPLASH
# ============================================

IMAGE_QUERIES = {
    "crm": ["business technology", "office work", "automation"],
    "video": ["video production", "camera cinema", "filmmaking"],
    "default": ["technology", "future", "innovation", "AI"],
}

def get_image_url(post_type: str) -> str:
    if "crm" in post_type:
        queries = IMAGE_QUERIES["crm"]
    elif "video" in post_type:
        queries = IMAGE_QUERIES["video"]
    else:
        queries = IMAGE_QUERIES["default"]
    
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
# ПУБЛИКАЦИЯ — ОСНОВНОЙ ПОСТ (13:00 и 19:00)
# ============================================

async def publish_post(time_of_day: str = "morning"):
    try:
        post_type = get_post_type(time_of_day)
        logger.info(f"📝 Тип поста: {post_type} ({time_of_day})")
        
        text = generate_post(post_type)
        logger.info(f"✅ Текст сгенерирован, {len(text)} символов")
        
        # Защита от слишком длинных постов
        if len(text) > 1024:
            truncated = text[:1010]
            last_dot = max(
                truncated.rfind('.'),
                truncated.rfind('!'),
                truncated.rfind('?'),
                truncated.rfind('\n\n')
            )
            if last_dot > 500:
                text = truncated[:last_dot + 1]
            else:
                last_space = truncated.rfind(' ')
                text = truncated[:last_space] + '.'
            logger.warning(f"⚠️ Текст обрезан до {len(text)} символов")
        
        image_url = get_image_url(post_type)
        bot = Bot(token=BOT_TOKEN)
        
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
    """Утренний пост в 13:00 Ташкент (8:00 UTC)"""
    await publish_post("morning")


async def publish_evening():
    """Вечерний пост в 19:00 Ташкент (14:00 UTC)"""
    await publish_post("evening")


# ============================================
# ПРИВЕТСТВИЕ — 7:00 Ташкент (2:00 UTC)
# ============================================

async def publish_greeting():
    try:
        greeting = get_morning_greeting()
        # Добавляем хештеги
        hashtags = "\n\n" + get_hashtags(topic="general")
        
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=greeting + hashtags
        )
        
        logger.info("✅ Утреннее приветствие опубликовано")
        
    except Exception as e:
        logger.error(f"❌ Ошибка приветствия: {e}")


# ============================================
# ДНЕВНОЙ ПОСТ — 17:00 Ташкент (12:00 UTC) — AI новости
# ============================================

# Индекс для последовательной публикации (не повторяться сразу)
_daily_post_index = 0

async def publish_daily_ai_post():
    """Публикует один из 30 готовых AI постов в 17:00."""
    global _daily_post_index
    
    try:
        # Берём пост по индексу
        post_text = DAILY_AI_POSTS[_daily_post_index % len(DAILY_AI_POSTS)]
        _daily_post_index += 1
        
        # Добавляем CTA и хештеги
        cta = get_cta()
        hashtags = "\n\n" + get_hashtags(topic="news")
        
        full_text = post_text + cta + hashtags
        
        # Картинка
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


# ============================================
# ОПРОСЫ
# ============================================

async def publish_poll():
    try:
        poll = random.choice(POLLS)
        bot = Bot(token=BOT_TOKEN)
        await bot.send_poll(
            chat_id=CHANNEL_USERNAME,
            question=poll["question"],
            options=poll["options"],
            is_anonymous=True
        )
        logger.info("✅ Опрос опубликован!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка опроса: {e}")


# ============================================
# KEEP-ALIVE
# ============================================

async def keep_alive_ping():
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
        await publish_post("morning")
    
    scheduler = AsyncIOScheduler(timezone="UTC")
    
    # ===== РАСПИСАНИЕ (UTC время) =====
    # ВАЖНО: бот работает по UTC, не по Tashkent
    # Ташкент = UTC + 5
    
    # 7:00 Ташкент = 2:00 UTC — Утреннее приветствие
    scheduler.add_job(
        publish_greeting,
        CronTrigger(hour=2, minute=0),
        id="greeting",
        replace_existing=True
    )
    
    # 13:00 Ташкент = 8:00 UTC — Утренний пост (серия)
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
    
    # 19:00 Ташкент = 14:00 UTC — Вечерний пост (серия)
    scheduler.add_job(
        publish_evening,
        CronTrigger(hour=14, minute=0),
        id="evening_post",
        replace_existing=True
    )
    
    # Опросы: Пн, Ср, Пт в 20:00 Ташкент = 15:00 UTC
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
    logger.info("🚀 Бот запущен v2.0. 4 поста в день + опросы 3 раза в неделю.")
    logger.info("📅 Расписание (Ташкент): 7:00 / 13:00 / 17:00 / 19:00")
    
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
