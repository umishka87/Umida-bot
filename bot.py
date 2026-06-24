# -*- coding: utf-8 -*-
"""
Telegram-бот для канала @AiContentCreatorUZ — ВЕРСИЯ 4.0 (финальная)

ЧТО ВНУТРИ:
- 20 постов на 10 дней (2 поста в день: 10:00 и 19:00 Ташкент)
- Ротация CTA и хештегов
- Опросы Пн/Ср/Пт
- Все промпты (Nano Banana 2, Kling, Hollywood, еда, одежда)

КЛЮЧЕВЫЕ ИСПРАВЛЕНИЯ:
- Индекс поста вычисляется ИЗ ДАТЫ (не из файла). На Railway /tmp стирается
  при каждой перезаливке, поэтому файл не спасал от повторов. Теперь день
  цикла = (сегодня - EPOCH) % 10. Сбросить нечего, повтор внутри цикла невозможен.
- Длинные посты (промпты) уходят ОТДЕЛЬНЫМ ТЕКСТОВЫМ сообщением (лимит 4096),
  чтобы промпт не обрезался. Короткие — с картинкой (лимит подписи 1024).
- Факты обновлены: MidJourney V8.1, Higgsfield "Soul Cinema", Claude Fable 5,
  ChatGPT 900 млн/нед, Microsoft 15 000+ сокращений, Klarna (с нюансом).

Расписание (сервер в UTC, Ташкент = UTC+5):
  10:00 Ташкент = 05:00 UTC — утренний пост (новости)
  19:00 Ташкент = 14:00 UTC — вечерний пост (промпт/совет)
  20:00 Ташкент = 15:00 UTC — опрос (Пн/Ср/Пт)
"""

import os
import random
import logging
from datetime import datetime, date, timezone, timedelta
import asyncio

import requests
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# ============================================
# НАСТРОЙКИ
# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_USERNAME = "@AiContentCreatorUZ"
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
INSTAGRAM_URL = "https://www.instagram.com/umishka_abdukarimova?utm_source=qr"

PUBLISH_ON_STARTUP = False
TELEGRAM_CAPTION_LIMIT = 1024

# День цикла считается от этой даты. 10-дневный цикл.
EPOCH = date(2026, 1, 1)
CYCLE_DAYS = 10

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)


# ============================================
# ИНДЕКС ИЗ ДАТЫ (вместо файла) — фикс повторов
# ============================================
def cycle_index() -> int:
    """0..9 — какой день 10-дневного цикла сегодня (по UTC-дате)."""
    today = datetime.now(timezone.utc).date()
    return (today - EPOCH).days % CYCLE_DAYS


# ============================================
# ХЕШТЕГИ — ТОЛЬКО РАБОЧИЕ (одобренный список)
# ============================================
HASHTAGS_MAIN = ["#uzbekistan", "#tashkent", "#toshkent", "#uzb", "#uzbek", "#uzbekiston", "#tashkentcity"]
HASHTAGS_REGIONS = ["#andijon", "#namangan", "#samarkand", "#buxoro", "#fargona"]
HASHTAGS_TELEGRAM = ["#telegram_yulduzlari", "#zortv", "#yulduzlari"]
HASHTAGS_CULTURE = ["#uzbekcha", "#uzbegim", "#uzbeks"]


def get_hashtags() -> str:
    selected = []
    selected += random.sample(HASHTAGS_MAIN, 4)
    selected += random.sample(HASHTAGS_REGIONS, 2)
    selected += random.sample(HASHTAGS_TELEGRAM, 2)
    selected += random.sample(HASHTAGS_CULTURE, 2)
    return " ".join(selected)


# ============================================
# CTA — ротация (с Instagram и без)
# ============================================
CTA_LIST = [
    f"\n\n📸 Mening ishlarim: {INSTAGRAM_URL}",
    f"\n\n💼 Brendingiz uchun AI-video kerakmi? {INSTAGRAM_URL}",
    f"\n\n🎬 AI-reklama namunalari: {INSTAGRAM_URL}",
    "\n\n🔥 Foydali bo'lsa — yurakcha bosing",
    "\n\n💾 Postni saqlab qo'ying — kerak bo'ladi",
    "\n\n💬 Savollar bormi? Sharhlarda yozing",
    "\n\n📤 Do'stingizga yuboring — unga ham foydali",
]


def get_cta() -> str:
    return random.choice(CTA_LIST)


# ============================================
# УТРЕННИЕ ПОСТЫ (10:00) — новости. Индекс 0..9 = день цикла.
# ============================================
MORNING_POSTS = [
    # ---- День 1: MidJourney V8.1 ----
    """🆕 MidJourney V8.1 — sifat yangi darajada

Hurmatli do'stlar, MidJourney'ning eng yangi versiyasi V8.1 endi asosiy versiyaga aylandi.

Yangiliklar:

🎯 Native 2K (HD) — alohida upscale kerak emas
⚡ 4-5 barobar tezroq generatsiya
📝 Matn yozish aniqlashdi — logotip va banner uchun
🧠 Murakkab promptlarni yaxshiroq tushunadi

V8.1 Syntx agregatorida ham bor.

Kim uchun muhim:
✅ Dizaynerlar
✅ Brending
✅ Poster va banner
✅ Mahsulot reklamasi

Reklama uchun MidJourney + Kling video = eng kuchli juftlik 2026 yilda.""",

    # ---- День 2: Higgsfield Arena Zero (Soul Cinema) ----
    """🎬 Higgsfield AI-serial yaratdi — "Arena Zero"

Hurmatli do'stlar, Higgsfield'ning "Soul Cinema" vositasi yordamida to'liq AI bilan yaratilgan 10 daqiqalik ilmiy-fantastik serial chiqdi.

Sof AI:
✅ Personajlar — AI
✅ Sahnalar — AI
✅ Kamera harakati — AI
✅ Yorug'lik va musiqa — AI
✅ Atigi 4 kishilik jamoa

Nima anglatadi:

Kichik studiyalar endi Netflix darajasidagi kontent qila oladi — million dollar byudjet kerak emas.

Real oqibatlar:
🎯 Reklama studiyalari qisqaradi
🎯 Kichik kreatorlar katta loyiha qila oladi
🎯 Kontent narxi keskin tushadi

Siz ham qila olasiz. Higgsfield obunasi $30/oydan.""",

    # ---- День 3: Grok 4.3 ----
    """🆕 Grok 4.3 (xAI'dan) — endi PDF va slaydlar

Hurmatli do'stlar, Elon Musk kompaniyasi xAI yangi versiya chiqardi — Grok 4.3.

Nima yangi:

📄 PDF fayllar
📊 Slaydlar (PowerPoint)
📈 Jadvallar (Excel)
📝 Hujjatlar (Word)

Ya'ni: ilgari matnni boshqa joyda fayl qilish kerak edi. Endi Grok hammasini o'zi qiladi.

Kim uchun foydali:
✅ Biznes — taqdimotlar tezroq
✅ O'qituvchilar — material
✅ Talabalar — kursovoy ishlar
✅ Marketing — hisobotlar

Qayerda: X Premium va SuperGrok obunalari orqali.

X'da bo'lmasangiz — ChatGPT yoki Claude ham bu ishlarni yaxshi bajaradi.""",

    # ---- День 4: Google Vids + Veo 3.1 ----
    """🆕 Google Vids endi Veo 3.1 va Lyria 3 bilan ishlaydi

Hurmatli do'stlar, Google video-redaktori "Vids" ichiga kuchli AI qo'shildi.

Yangiliklar:

🎬 Veo 3.1 — video bevosita Vids ichida generatsiya
🎵 Lyria 3 — musiqa va ovoz uchun

Nima muhim:

✅ Bir dasturdan boshqasiga o'tish kerak emas
✅ Hammasi bir joyda — video, ovoz, musiqa
✅ Reklama uchun katta tejov

Google bozorda Adobe va CapCut'ga raqobat boshlayapti.

Bu kontent yaratuvchilar uchun ajoyib — yagona joyda hamma vosita.""",

    # ---- День 5: Claude Fable 5 (вместо Mythos) ----
    """🆕 Anthropic eng kuchli modelini ommaga chiqardi — Claude Fable 5

Hurmatli do'stlar, Claude'ni yaratuvchi Anthropic yangi kuchli model chiqardi.

Nima ma'lum:

🎯 Yangi model — Claude Fable 5
📊 Hozirgi Opus 4.8 bilan bir qatorda eng kuchlilardan
🔬 Xavfli sohalarda (kiberxavfsizlik, biologiya) himoya o'rnatilgan
✅ Pullik obunachilar va bizneslar uchun ochiq

Nima muhim:

Anthropic'da "Mythos" degan o'ta kuchli model bor edi, lekin u faqat tanlangan kompaniyalarga berilgan. Fable 5 — shu darajadagi, ammo ommaga ochiq model.

Claude — kod va matn ishi uchun eng yaxshilaridan. Ssenariy, post matni, tarjima — yuqori sifatda.

AI poygasi tezlashyapti. Kuzatib boring.""",

    # ---- День 6: AdCreative.ai ----
    """🆕 AdCreative.ai — reklama bannerlari uchun AI

Hurmatli do'stlar, foydali xizmat — AdCreative.ai.

Nima qila oladi:

🎨 Reklama banner generatsiya
✍️ Sotuvga moslangan matnlar
🎯 Sarlavhalar
🖼️ Vizual uslublar
📊 To'liq reklama kampaniyalari

Bir necha soniyada — vaqtni tejaydi.

Kim uchun:
✅ Marketing
✅ Kichik biznes
✅ Instagram reklamasi
✅ E-commerce do'konlar

Ilgari dizayner + marketolog kerak edi. Endi bitta vosita ko'p ishni qiladi.

AI har soha uchun yechim taklif qiladi.""",

    # ---- День 7: Gemini import ----
    """🆕 Google Gemini endi ChatGPT va Claude tarixini ko'chiradi

Hurmatli do'stlar, Google katta yangilik qildi.

Nima yangi:

📥 Gemini'da yangi funksiya — boshqa AI-xizmatlardan suhbat tarixi va "xotira"ni import qilish mumkin

Bu nima anglatadi:

ChatGPT yoki Claude'dan Gemini'ga o'tsangiz — noldan boshlash shart emas. Eski suhbatlaringiz ko'chiriladi.

Nima muhim:

🎯 AI-xizmatlar orasida raqobat keskinlashdi
🎯 Platforma almashtirish oson bo'ldi

Diqqat: ko'chirilgan suhbatlar Google serverida saqlanadi. Maxfiy ma'lumot yuklamang.

Qaysi AI'ni asosiy qilib ishlatasiz?""",

    # ---- День 8: AI инвестиции в регионе ----
    """🆕 Mintaqada AI investitsiyalari tezlashyapti

Hurmatli do'stlar, MDH mintaqasida AI bo'yicha yirik loyihalar paydo bo'lyapti.

Masalan Armanistonda:

💰 Yirik investitsiya
🏢 Yangi AI data-centr
🤝 Xalqaro texnologiya kompaniyalari hamkor

Bu nima anglatadi:

🎯 Mintaqada AI quvvati o'sayapti
🎯 Lokal AI-xizmatlar paydo bo'ladi
🎯 AI mutaxassislar uchun ish o'rinlari

O'zbekistonda AI hozir bo'sh bozor. Birinchilar eng yaxshi joyni egallaydi. Bu sizning imkoniyatingiz.

Hozir o'rganing — keyin kech bo'ladi.""",

    # ---- День 9: ChatGPT 900 млн ----
    """📊 ChatGPT — haftada 900 mln foydalanuvchi

Hurmatli do'stlar, bu raqamga e'tibor bering.

ChatGPT statistikasi:

🌍 Haftada 900 mln aktiv foydalanuvchi (2026)
📈 Oyiga 1 milliarddan oshdi
⚡ Internet 100 mln'ga 7 yil kerak edi, ChatGPT — bir necha oy

Bu tarixdagi eng tez tarqalgan texnologiya.

Nima anglatadi sizga:

🎯 AI endi "kelajak" emas — bugun
🎯 AI'ni o'rganmoq — yangi savod, 100 yil oldingi o'qish-yozish kabi

Savol o'zingizga: siz qancha vaqt AI bilan ishlaysiz — har kuni? Haftada bir? Hech qachon?

Javob — sizning kelajagingiz.""",

    # ---- День 10: тренды 2026 (без HeyGen) ----
    """🚀 AI trendlari 2026 — nima muhim

Hurmatli do'stlar, bu yil AI dunyosida asosiy trendlar.

Eng muhimlari:

1️⃣ Native ovoz va lablar — video to'liq ovozli
2️⃣ Uzun videolar — 30-60 soniya endi standart
3️⃣ Personaj consistency — bir personaj turli sahnada bir xil
4️⃣ Multi-shot — bitta promptdan butun hikoya
5️⃣ 4K vertikal — Reels va TikTok uchun
6️⃣ AI + real foto — odam real, fon AI
7️⃣ Gapiruvchi avatarlar — alohida katta yo'nalish (keyingi oyda batafsil)
8️⃣ Open-source modellar — kompyuterda bepul
9️⃣ Real vaqtli generatsiya — yaqin kelajakda
🔟 Tamoyillar muhim — yorug'lik, kompozitsiya, prompt strukturasi

Trendlarni kuzating, lekin chuqurlikka boring.""",
]


# ============================================
# ВЕЧЕРНИЕ ПОСТЫ (19:00) — промпты и психология. Индекс 0..9 = день цикла.
# ============================================
EVENING_POSTS = [
    # ---- День 1: PROMPT "Fight Club" avatar ----
    """🎨 PROMPT: Avatar "Fight Club" uslubida

Hurmatli do'stlar, bugun tayyor prompt — o'zingizga kinostil avatar.

NIMA KERAK:
1. Sizning fotosurat (yuz aniq)
2. Referens fotosurat (kerakli uslub)
3. Nano Banana 2 — botda yoki saytda

PROMPT (nusxa oling):

Use Image 1 as face reference (identity, features, skin tone, hair). Use Image 2 as scene reference (lighting, pose, atmosphere). Replace face in Image 2 with person from Image 1. Keep identity, facial structure, skin tone, natural details from Image 1. Body should naturally match face — not a simple face swap. Keep expression, camera angle, dramatic lighting from Image 2. Blend skin tones perfectly, match shadows and color grading. Keep background, clothing, environment identical to Image 2. Ultra-realistic, high detail, cinematic lighting, sharp focus, natural skin texture, professional photography.

QANDAY ISHLATISH:
1. Nano Banana 2 ga kiring
2. Ikkita rasm yuklang (siz + referens)
3. Promptni qo'ying
4. 30 soniya kuting
5. Tayyor!

Maslahat: referens rasmi sifatli bo'lsin — yorug'lik aniq.""",

    # ---- День 2: PROMPT сюрреализм ----
    """🎨 PROMPT: Syurrealistik portret fashion uslubida

Hurmatli do'stlar, bugun tayyor prompt — Vogue darajasidagi portret.

KONSEPT: bitta odam ikki versiyada. Kattalashgan yuz sochlaridan ikkinchi versiya osilib turadi.

NIMA KERAK:
1. Sizning fotosurat
2. Nano Banana 2

PROMPT (nusxa oling):

Create a surreal high-fashion portrait with extreme scale distortion. Two versions of the same person in frame. Foreground: massive close-up of the face dominating the top-center, looking down toward viewer, playful expression, natural skin texture. Background: full-length version of the same person swinging from the giant hair of the foreground head, laughing, confident, wearing a streetwear jacket. Environment: lush green meadow with tall wildflowers reaching into the sky. Bright editorial lighting, crisp definition, rim light. Wide-angle lens 24-28mm effect, extreme foreground scale exaggeration. Mood: playful, bold, fashion-campaign energy. Vibrant tones, rich greens, magazine editorial finish. Ultra-realistic photography, high micro-detail, no CGI gloss, no text, no watermark.

QANDAY:
1. Nano Banana 2 ga rasm yuklang
2. Promptni qo'ying
3. Generatsiya — 1-2 marta sinang

Maslahat: "wide-angle lens" so'zlari dramatik effekt beradi — olib tashlamang.""",

    # ---- День 3: психология одиночества ----
    """💬 "Hech kim meni tushunmaydi" — AI-kreator yolg'izligi

Hurmatli do'stlar, bu post shaxsiy. Lekin bilaman — siz ham buni his qilasiz.

Qanday ko'rinadi:

🌙 Tunda promptlar yozasiz
🌙 Oila: "Yana kompyuter? Boshqa ish yo'q?"
🌙 5 soat ishladingiz, lekin "rasm chizdim" deyish bolaning ishidek tuyuladi
🌙 O'sishingiz "nimadir g'alati" deb baholanadi

Bu normalmi? Mutlaqo.

AI-kreator kasbi yangi. Yaqinlaringiz nimani his qilayotganingizni bilmaydi.

Nima qilish kerak:

✅ Yaqinlardan to'liq tushunish kutmang
✅ Boshqa kreatorlar bilan ulashing — Telegram, Instagram, YouTube
✅ Ishingizni faktlar bilan o'lchang

Kuchli kreatorlar yolg'izlikdan qochmaydi — ular uni tushunadi va hamjamiyatga tayanadi.

Bu — kasbda yetuklik.""",

    # ---- День 4: старт с Claude Code (заменён выдуманный топ-10) ----
    """💡 Claude Code bilan dasturlashni qanday boshlash

Hurmatli do'stlar, dasturchi bo'lmasangiz ham AI yordamida kod yozish mumkin. Claude Code — buning eng oson yo'li.

NIMADAN BOSHLASH:

1. Claude'ning rasmiy hujjatlari (docs.claude.com) — bepul, qadamba-qadam
2. Kichik loyihadan boshlang — oddiy bot yoki bitta sahifa
3. Vazifani sodda til bilan tushuntiring — Claude kodni yozadi
4. Xato chiqsa — xatoni nusxalab Claude'ga bering, u tuzatadi

MASLAHATLAR:

✅ Katta vazifani kichik qadamlarga bo'ling
✅ "Nega bunday?" deb so'rang — Claude tushuntiradi, siz o'rganasiz
✅ Ishlagan kodni saqlab boring

Til to'siq emas — minimal ingliz bilim kifoya.

Men ham shu yo'l bilan o'rgandim. Siz ham qila olasiz.

Dasturlashni o'rganmoqchimisiz? Sharhlarda yozing.""",

    # ---- День 5: PROMPT Kling 3.0 ----
    """🎬 PROMPT: Kinematografik portret Kling 3.0 da

Hurmatli do'stlar, bugun prompt Kling 3.0 uchun — reklama darajasidagi natija.

NIMA KERAK:
1. Sizning yoki mahsulot rasmi
2. Kling 3.0

PROMPT (nusxa oling):

Cinematic portrait shot, professional model, natural makeup, soft golden hour lighting, shallow depth of field, slow push-in camera movement, warm color grading, film grain texture, 4K quality, photorealistic, smooth movement, natural facial expressions, subtle smile transitioning to a confident look, eyes following the light source, hair slightly moving in a gentle breeze, background blurred warm bokeh, editorial fashion photography style.

QANDAY:
1. Kling.ai ga kiring (bepul kunlik kredit bor)
2. Image-to-video tanlang
3. Rasm yuklang
4. Promptni qo'ying
5. Sifat: HD yoki 4K, davomiyligi 5-10 soniya
6. Generatsiya

Natija: reklama darajasidagi video — sosial tarmoq, brending, portfel uchun.

Kling 3.0 — 2026 yilning yetakchi video modellaridan. Bepul tarif tijoriy ish uchun emas.""",

    # ---- День 6: совет 1+1+1 ----
    """💡 "1+1+1 qoidasi" — qaysi vositalarni tanlash

Hurmatli do'stlar, ko'pchilik so'raydi: "10 ta model bor — qaysi birini tanlash?"

XATO YO'L: hammasini sinab ko'rish. Bu charchatadi, natija yo'q.

TO'G'RI YO'L: 1+1+1 qoidasi.

🎨 1 ta model rasm uchun (MidJourney yoki Flux yoki Nano Banana 2)
🎬 1 ta model video uchun (Kling yoki Runway yoki Veo)
🧠 1 ta yordamchi matn uchun (ChatGPT yoki Claude)

Shu 3 ta vositada 3-6 oy chuqur ishlang.

Nima uchun ishlaydi:

🎯 Bir vositada 100 marta ishlash — 10 ta vositada 1 martadan kuchli
🎯 Mijoz tajribangizni payqaydi
🎯 Modellar o'zgaradi, tamoyillar bir xil — tamoyillarni o'rganing

Yangi model chiqdi? 30 daqiqa sinang. Yoqdi — davom eting. Yo'q — eskingizga qayting.

AI marafon, sprint emas.""",

    # ---- День 7: PROMPT еда ----
    """🍔 PROMPT: Restoran taom rasmi Nano Banana 2 da

Hurmatli do'stlar, restoran va kafe egalari — bu siz uchun.

NIMA KERAK:
1. Taomning rasmi
2. Nano Banana 2

PROMPT (nusxa oling):

Professional food photography of [dish name], close-up macro shot, steam rising, glistening textures, natural ingredients visible, golden warm lighting from the side, dark moody background, shallow depth of field, water droplets on fresh ingredients, appetizing colors, rich saturation, food magazine editorial style, photorealistic, ultra detailed textures, professional studio lighting, beautiful plating, garnishes visible, perfect composition, mouth-watering presentation.

[dish name] o'rniga yozing: "lagman" yoki "plov" yoki "shashlik" — istalgan taom.

QANDAY:
1. Nano Banana 2 ga kiring
2. Taom rasmini yuklang
3. Promptni qo'ying
4. Generatsiya

Natija: Instagram va menyu uchun professional rasm. Fotografga $200-500 emas — arzon.

Maslahat: "appetizing", "steaming hot", "fresh" so'zlari natijani tabiiy qiladi.""",

    # ---- День 8: PROMPT одежда (Kling) ----
    """👗 PROMPT: Kiyim brendi uchun video Kling'da

Hurmatli do'stlar, kiyim do'koni egalari — bu siz uchun.

NIMA KERAK:
1. Kiyim katalog rasmi
2. Kling 3.0

PROMPT (nusxa oling):

Fashion editorial video, beautiful model wearing an elegant outfit, walking confidently through an urban street, golden hour lighting, slow motion 60fps, cinematic camera following the model, soft wind moving the fabric naturally, vibrant city background slightly blurred, professional fashion photography style, model looking confidently at camera with a subtle smile, hair flowing naturally, clothes moving with movement, color graded for Instagram aesthetic, 4K quality, smooth camera tracking shot, 10 seconds duration.

QANDAY:
1. Kling.ai ga kiring
2. Image-to-video tanlang
3. Kiyim rasmini yuklang
4. Promptni qo'ying
5. Sifat HD, davomiyligi 10 soniya

Natija: reklama agentligi darajasidagi video — Instagram, TikTok uchun.

Kichik do'kon endi katta brend kabi reklama qila oladi.""",

    # ---- День 9: AI — новая грамотность (факты обновлены) ----
    """🧠 AI — yangi savod 2026 yilda

Hurmatli do'stlar, e'tibor bering bu fikrga.

100 yil oldin: o'qish-yozishni bilmagan qiynalardi.
50 yil oldin: kompyuterni bilmagan yaxshi ish topa olmadi.
Bugun: AI bilan ishlashni bilmagan ortda qoladi.

Statistika:

📊 ChatGPT — haftada 900 mln foydalanuvchi
📊 Microsoft 2025-yilda 15 000+ ish o'rnini qisqartirdi, AI'ga sarmoya yo'naltirib
📊 Klarna AI'si 700 operator ishini bajardi — lekin keyin sifat uchun yana odamlarni ishga oldi

Muhim xulosa: AI odamni butunlay almashtirmaydi — u kuchaytiradi. Eng yaxshi natija: AI + odam.

Nima qilish:

✅ Kuniga 30 daqiqa AI bilan
✅ Bittasini chuqur o'rganing (ChatGPT yoki Claude)
✅ O'z ishingizga moslang

Bugun boshlang. Erta kech bo'ladi.""",

    # ---- День 10: PROMPT Hollywood портрет ----
    """🎥 PROMPT: Kinematografik portret Hollywood uslubida

Hurmatli do'stlar, yakuniy bonus — Hollywood uslubidagi portret.

NIMA KERAK:
1. Sizning fotosurat
2. Nano Banana 2

PROMPT (nusxa oling):

Cinematic close-up portrait in Hollywood film style, professional lighting setup with key light from the side, soft fill light, dramatic shadows on the opposite side, shot on a cinema camera, 85mm lens, shallow depth of field, photorealistic skin texture with natural pores visible, intense gaze, subtle expression, warm cinematic color grading, atmospheric haze, slight film grain, professional cinematography, magazine editorial quality, sharp focus on the eyes, hair detailed with light catching individual strands, neck and shoulders visible, blurred background with cinematic bokeh, ultra-realistic, no CGI gloss, natural human imperfections preserved, museum-quality portrait photography.

QANDAY:
1. Nano Banana 2 ga kiring
2. Rasm yuklang
3. Promptni qo'ying
4. Generatsiya, 2-3 marta sinang

Natija: LinkedIn, sayt, portfolio uchun professional portret.""",
]


# ============================================
# КАРТИНКА ЧЕРЕЗ UNSPLASH
# ============================================
IMAGE_QUERIES = ["artificial intelligence", "ai technology", "future technology", "neural network", "digital art", "creative technology"]


def get_image_url():
    if not UNSPLASH_ACCESS_KEY:
        return None
    try:
        r = requests.get(
            "https://api.unsplash.com/photos/random",
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            params={"query": random.choice(IMAGE_QUERIES), "orientation": "landscape"},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()["urls"]["regular"]
        logger.warning("Unsplash status %s", r.status_code)
    except Exception as e:
        logger.warning("Unsplash xato: %s", e)
    return None


# ============================================
# ПУБЛИКАЦИЯ
# ============================================
async def publish_post(post_text: str):
    """Короткий пост -> с картинкой (caption). Длинный (промпт) -> отдельным текстом, БЕЗ обрезки."""
    full_text = post_text + get_cta() + "\n\n" + get_hashtags()
    try:
        if len(full_text) <= TELEGRAM_CAPTION_LIMIT:
            image_url = get_image_url()
            if image_url:
                await bot.send_photo(chat_id=CHANNEL_USERNAME, photo=image_url, caption=full_text)
                logger.info("Опубликовано с картинкой (%s симв.)", len(full_text))
                return
        # длинный пост или нет картинки -> обычное сообщение (до 4096)
        await bot.send_message(chat_id=CHANNEL_USERNAME, text=full_text, disable_web_page_preview=False)
        logger.info("Опубликовано текстом (%s симв.)", len(full_text))
    except Exception as e:
        logger.error("Ошибка публикации: %s", e)


async def publish_morning():
    idx = cycle_index()
    logger.info("📰 Утренний пост, день цикла #%s", idx + 1)
    await publish_post(MORNING_POSTS[idx])


async def publish_evening():
    idx = cycle_index()
    logger.info("🎨 Вечерний пост, день цикла #%s", idx + 1)
    await publish_post(EVENING_POSTS[idx])


# ============================================
# ОПРОСЫ — Пн/Ср/Пт 20:00 Ташкент (15:00 UTC)
# ============================================
POLLS = [
    {"question": "Qaysi AI-rasm modelidan foydalanasiz? 🎨", "options": ["MidJourney", "Nano Banana 2", "Flux", "Hech qaysi"]},
    {"question": "AI bilan kuniga qancha ishlaysiz? ⏰", "options": ["1 soatdan kam", "1-3 soat", "3-5 soat", "5+ soat"]},
    {"question": "Qaysi AI-video model qiziq? 🎬", "options": ["Kling 3.0", "Runway", "Veo 3.1", "Pika"]},
    {"question": "AI ishingizni o'zgartirdimi? 💼", "options": ["Ha, juda", "Ozgina", "Hozircha yo'q", "Sinab ko'ryapman"]},
    {"question": "Yangi AI-vositalarni qanchalik kuzatasiz? 👀", "options": ["Har kuni", "Haftada bir", "Oyiga bir", "Tasodifan"]},
]


async def publish_poll():
    poll = random.choice(POLLS)
    try:
        await bot.send_poll(
            chat_id=CHANNEL_USERNAME,
            question=poll["question"],
            options=poll["options"],
            is_anonymous=True,
        )
        logger.info("Опрос опубликован")
    except Exception as e:
        logger.error("Ошибка опроса: %s", e)


# ============================================
# KEEP-ALIVE
# ============================================
async def keep_alive_ping():
    tashkent = timezone(timedelta(hours=5))
    logger.info("💚 Keep-alive — Ташкент %s", datetime.now(tashkent).strftime("%H:%M"))


# ============================================
# MAIN
# ============================================
async def main():
    await bot.initialize()
    me = await bot.get_me()
    logger.info("Бот подключён: @%s", me.username)

    if PUBLISH_ON_STARTUP:
        await publish_morning()

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(publish_morning, CronTrigger(hour=5, minute=0, timezone="UTC"), id="morning", replace_existing=True)
    scheduler.add_job(publish_evening, CronTrigger(hour=14, minute=0, timezone="UTC"), id="evening", replace_existing=True)
    scheduler.add_job(publish_poll, CronTrigger(day_of_week="mon,wed,fri", hour=15, minute=0, timezone="UTC"), id="poll", replace_existing=True)
    scheduler.add_job(keep_alive_ping, IntervalTrigger(minutes=10), id="keep_alive", replace_existing=True)
    scheduler.start()

    logger.info("🚀 Бот v4.0 запущен. Сегодня день цикла #%s", cycle_index() + 1)
    logger.info("📅 10:00 (новости) и 19:00 (промпты), опросы Пн/Ср/Пт 20:00 (Ташкент)")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
