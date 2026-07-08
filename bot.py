# -*- coding: utf-8 -*-
"""
Telegram-бот для канала @AiContentCreatorUZ — ВЕРСИЯ 5.0
20 дней контента, 2 поста в день (40 постов).

СТРУКТУРА (день цикла 1..20):
  УТРО (10:00 Ташкент = 05:00 UTC):
    - обычные дни -> НОВОСТЬ
    - дни 5, 10, 15, 20 -> ОБУЧЕНИЕ (мини-урок про Krea/приёмы)
  ВЕЧЕР (19:00 Ташкент = 14:00 UTC):
    - обычные дни -> ПРОМПТ
    - дни 5, 10, 15, 20 -> БЕСПЛАТНЫЕ РЕСУРСЫ

ФИКС ПОВТОРОВ:
  День цикла = (сегодня - EPOCH) % 20. Считается из даты, файл не нужен,
  при перезапуске/перезаливке ничего не сбрасывается.

ДЛИННЫЕ ПОСТЫ (промпты) -> уходят отдельным ТЕКСТОМ (до 4096), не обрезаются.
КОРОТКИЕ -> с картинкой (Unsplash), лимит подписи 1024.

Без опросов. CTA (Instagram) и хештеги бот подставляет сам.
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

EPOCH = date(2026, 1, 1)
CYCLE_DAYS = 20
LESSON_DAYS = {5, 10, 15, 20}   # дни, когда утро=обучение, вечер=бесплатные ресурсы

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)


# ============================================
# ИНДЕКС ИЗ ДАТЫ
# ============================================
def cycle_day() -> int:
    """1..20 — день цикла (по UTC-дате)."""
    today = datetime.now(timezone.utc).date()
    return (today - EPOCH).days % CYCLE_DAYS + 1


# ============================================
# ХЕШТЕГИ (одобренный список)
# ============================================
HASHTAGS_MAIN = ["#uzbekistan", "#tashkent", "#toshkent", "#uzb", "#uzbek", "#uzbekiston", "#tashkentcity"]
HASHTAGS_REGIONS = ["#andijon", "#namangan", "#samarkand", "#buxoro", "#fargona"]
HASHTAGS_TELEGRAM = ["#telegram_yulduzlari", "#zortv", "#yulduzlari"]
HASHTAGS_CULTURE = ["#uzbekcha", "#uzbegim", "#uzbeks"]


def get_hashtags() -> str:
    s = []
    s += random.sample(HASHTAGS_MAIN, 4)
    s += random.sample(HASHTAGS_REGIONS, 2)
    s += random.sample(HASHTAGS_TELEGRAM, 2)
    s += random.sample(HASHTAGS_CULTURE, 2)
    return " ".join(s)


# ============================================
# CTA (ротация)
# ============================================
CTA_LIST = [
    f"\n\n📸 Mening ishlarim: {INSTAGRAM_URL}",
    f"\n\n💼 Brendingiz uchun AI-kontent kerakmi? {INSTAGRAM_URL}",
    f"\n\n🎬 AI-reklama namunalari: {INSTAGRAM_URL}",
    "\n\n🔥 Foydali bo'lsa — yurakcha bosing",
    "\n\n💾 Postni saqlab qo'ying — kerak bo'ladi",
    "\n\n💬 Savollar bormi? Sharhlarda yozing",
    "\n\n📤 Do'stingizga yuboring — unga ham foydali",
]


def get_cta() -> str:
    return random.choice(CTA_LIST)


# ============================================
# НОВОСТИ — 16 штук (утро обычных дней)
# ============================================
NEWS_POSTS = [
    # 1
    """🆕 OpenAI GPT-5.6 chiqardi — Sol, Terra, Luna

Hurmatli do'stlar, OpenAI uchta yangi model chiqardi: GPT-5.6 Sol, Terra va Luna.

Nima muhim:
✅ Sol — eng kuchli, kod va murakkab vazifalar uchun
✅ Terra — GPT-5.5 darajasida, lekin arzonroq
✅ Luna — eng tejamkor, ko'p ish uchun

Boshida faqat tanlangan hamkorlarga berildi, keyin hammaga ochilmoqda.

AI poygasi tezlashyapti — har oy yangi model. Bizga foyda: sifat oshadi, narx tushadi.""",
    # 2
    """🆕 Anthropic Claude Sonnet 5 chiqardi

Hurmatli do'stlar, Claude'ni yaratuvchi Anthropic yangi model chiqardi — Claude Sonnet 5.

Nima muhim:
✅ Bepul va Pro foydalanuvchilar uchun asosiy model bo'ldi
✅ Matn, kod, tahlil — yuqori sifatda
✅ Tez va ishonchli

Kreator uchun: ssenariy, post matni, tarjima, g'oyalar — hammasini kuchli bajaradi.

Claude'dan foydalanasizmi? Sharhlarda yozing.""",
    # 3
    """🆕 Google Gemma 4 — kompyuteringizda bepul ishlaydi

Hurmatli do'stlar, Google yangi ochiq model chiqardi — Gemma 4 12B.

Nima ajoyib:
✅ Internetsiz, o'z kompyuteringizda ishlaydi
✅ Atigi 16 GB xotira yetarli
✅ Matn, rasm va ovozni tushunadi
✅ Bepul

Bu shuni anglatadi: kuchli AI endi faqat bulutda emas, shaxsiy laptopda ham.""",
    # 4
    """🆕 NVIDIA Nemotron — bitta modelda ko'radi, eshitadi, o'qiydi

Hurmatli do'stlar, NVIDIA yangi model chiqardi — Nemotron 3 Nano Omni.

Nima muhim:
✅ Rasm, ovoz va matnni bitta modelda birlashtiradi
✅ Boshqa ochiq modellardan 9 barobar tezroq
✅ Hujjat, video, audio tahlilida yetakchi

Ochiq model — dasturchilar bepul ishlata oladi. AI tez rivojlanyapti.""",
    # 5
    """🆕 Xitoy AI'da yaqinlashyapti — GLM-5.2

Hurmatli do'stlar, Xitoyning Z.ai kompaniyasi arzon, lekin kuchli model chiqardi — GLM-5.2.

Nima muhim:
✅ Kod yozishda eng kuchli ochiq modellardan
✅ 1 million so'zgacha kontekst
✅ Ochiq litsenziya — o'z serveringizda ishlatasiz
✅ Amerika modellariga raqobat

AI endi faqat AQSH emas — dunyo poygasi. Bu narxni tushiradi.""",
    # 6
    """🆕 Google Gemini jonli tarjimon bo'ldi

Hurmatli do'stlar, Gemini'ga jonli tarjima qo'shildi — Live Translate.

Nima muhim:
✅ Suhbatni real vaqtda tarjima qiladi
✅ Ovozli muloqot uchun
✅ Google Meet va Translate ilovasida

Bu til to'sig'ini yo'q qiladi — chet ellik mijoz bilan ishlash osonlashadi.

Sizga qaysi til kerak bo'lardi? Sharhlarda yozing.""",
    # 7
    """🆕 MidJourney V8.1 — yangi standart

Hurmatli do'stlar, MidJourney'ning V8.1 versiyasi asosiy versiyaga aylandi.

Yangiliklar:
🎯 Native 2K (HD) — alohida upscale kerak emas
⚡ 4-5 barobar tezroq
📝 Matn (logotip, banner) aniqlashdi
🧠 Murakkab promptlarni yaxshiroq tushunadi

Reklama uchun MidJourney + Kling = eng kuchli juftlik 2026 yilda.""",
    # 8
    """🎬 Higgsfield AI-serial yaratdi — "Arena Zero"

Hurmatli do'stlar, Higgsfield'ning "Soul Cinema" vositasida to'liq AI bilan yaratilgan 10 daqiqalik ilmiy-fantastik serial chiqdi.

Sof AI:
✅ Personaj, sahna, kamera, ovoz — hammasi AI
✅ Atigi 4 kishilik jamoa

Nima anglatadi: kichik studiyalar endi million dollar byudjetsiz kontent qila oladi.

Kinoning kelajagi shunday.""",
    # 9
    """🆕 Google Vids endi Veo 3.1 bilan ishlaydi

Hurmatli do'stlar, Google video-redaktori "Vids" ichiga kuchli AI qo'shildi.

Yangiliklar:
🎬 Veo 3.1 — video bevosita Vids ichida generatsiya
🎵 Lyria 3 — musiqa va ovoz uchun

Nima muhim:
✅ Bir dasturdan boshqasiga o'tish kerak emas
✅ Video, ovoz, musiqa — bir joyda

Google Adobe va CapCut'ga raqobat boshlayapti.""",
    # 10
    """🆕 Gemini ChatGPT va Claude tarixini ko'chiradi

Hurmatli do'stlar, Google qiziq imkoniyat qo'shdi.

Nima yangi:
📥 Gemini'ga ChatGPT yoki Claude'dagi eski suhbatlarni ko'chirish mumkin

Bu nima anglatadi:
✅ Yangi AI'ga o'tsangiz — noldan boshlash shart emas
✅ Platforma almashtirish oson

Diqqat: ko'chirilgan suhbatlar Google serverida saqlanadi. Maxfiy ma'lumot yuklamang.""",
    # 11
    """📊 ChatGPT — haftada 900 mln foydalanuvchi

Hurmatli do'stlar, bu raqamga e'tibor bering.

✅ Haftada 900 mln aktiv foydalanuvchi
✅ Oyiga 1 milliarddan oshdi
✅ Tarixdagi eng tez tarqalgan texnologiya

Nima anglatadi sizga:
🎯 AI endi "kelajak" emas — bugun
🎯 AI'ni bilish — yangi savod, o'qish-yozish kabi

Siz qancha vaqt AI bilan ishlaysiz?""",
    # 12
    """🆕 GitHub Copilot pullik hisoblashga o'tdi

Hurmatli do'stlar, dasturchilar uchun mashhur GitHub Copilot to'lov tizimini o'zgartirdi.

Nima o'zgardi:
✅ Endi ishlatilganiga qarab to'lov (metered)
✅ "AI kreditlari" tizimi joriy etildi

Sabab: murakkab AI-kod sessiyalari qimmatga tushyapti, eski "cheksiz" tarif foydasiz bo'ldi.

Bu butun soha trendi — bepul davri asta tugayapti.""",
    # 13
    """🆕 OpenAI birjaga chiqishga tayyorlanyapti (IPO)

Hurmatli do'stlar, ChatGPT'ni yaratuvchi OpenAI rasman IPO'ga hujjat topshirdi.

Nima ma'lum:
✅ Kompaniya bahosi — 852 mlrd dollar
✅ Tez orada aksiyalar sotuvga chiqishi mumkin

Nima anglatadi: AI endi katta biznes va iqtisodning markazida. Bu sohaga pul va e'tibor oqib kelyapti.

AI'ni bilgan odam bu to'lqinda yutadi.""",
    # 14
    """🆕 Dunyoning birinchi AI-san'at muzeyi ochildi

Hurmatli do'stlar, Google Los-Anjelesda "Dataland" — dunyoning birinchi AI-san'at muzeyini quvvatladi.

Nima ajoyib:
✅ San'at asarlari real vaqtda AI tomonidan yaratiladi
✅ Interaktiv — tomoshabin bilan "gaplashadi"
✅ 25 000 kv.metr maydon

AI endi faqat vosita emas — san'at ham. Kelajak shu yerda boshlanyapti.""",
    # 15
    """🆕 xAI Grok 4.5 — tez orada ommaga

Hurmatli do'stlar, Elon Musk kompaniyasi xAI yangi model tayyorlayapti — Grok 4.5.

Nima ma'lum:
✅ Hozir SpaceX va Tesla'da yopiq sinovda
✅ Juda katta va kuchli model
✅ Yaqin oylarda ommaga chiqishi kutilmoqda

xAI har oy yangilik chiqaryapti. AI poygasi to'xtamayapti — kuzatib boring.""",
    # 16
    """🆕 Krea — 30 million foydalanuvchidan oshdi

Hurmatli do'stlar, Krea platformasi 30 milliondan ortiq foydalanuvchiga yetdi (191 mamlakat).

Nima uchun mashhur:
✅ 60+ AI-modelni bitta joyda beradi (Flux, Kling, Veo va boshqalar)
✅ Realtime Canvas — chizasiz, rasm darhol paydo bo'ladi
✅ Rasmni 22K gacha kattalashtirish (upscale)
✅ Bepul kunlik kredit bor

Bitta platformada ko'p vosita — vaqt tejaladi. (Krea haqida darslar oldinda!)""",
]


# ============================================
# ОБУЧЕНИЕ — 4 штуки (утро дней 5/10/15/20)
# ============================================
LESSON_POSTS = [
    # для дня 5
    """📚 DARS: Krea nima va Realtime Canvas qanday ishlaydi

Hurmatli do'stlar, bugun qisqacha — Krea nima.

Krea — brauzerda ishlaydigan AI-ijod platformasi. Bir joyda: rasm, video, upscale va 60+ model.

Eng qiziq narsa — Realtime Canvas:
✅ Siz oddiy shakl chizasiz yoki prompt yozasiz
✅ AI darhol (bir soniyada) real rasmga aylantiradi
✅ Kutish yo'q — o'zgartirasiz va natijani ko'rasiz

Nima uchun foydali: g'oyani tez sinash uchun zo'r. Boshlash bepul — karta shart emas.

Keyingi darslarda: upscale, negative prompt va o'lchamlar.""",
    # для дня 10
    """📚 DARS: Krea'da eski yoki xira fotoni yaxshilash (upscale)

Hurmatli do'stlar, bugun foydali ko'nikma — xira rasmni tiniq qilish.

Krea'da upscale — bu rasmni sifatini oshirib, kattalashtirish.

Qadamlar:
1. Krea'ga kiring, Enhance / Upscale bo'limini tanlang
2. Eski yoki xira rasmni yuklang
3. Sifat darajasini tanlang
4. Generatsiya — rasm tiniqroq bo'ladi

Kimga kerak:
✅ Do'kon — eski mahsulot rasmlari
✅ Ko'chmas mulk — xira interyer fotolar
✅ Shaxsiy — eski oilaviy suratlar

Maslahat: juda buzuq rasmni mukammal qilib bo'lmaydi, lekin ancha yaxshilaydi.""",
    # для дня 15
    """📚 DARS: Negative prompt — ortiqcha narsani olib tashlash

Hurmatli do'stlar, bugun muhim ustalik — negative prompt.

Oddiy prompt: nima KERAK ekanini yozasiz.
Negative prompt: nima KERAK EMAS ekanini yozasiz.

Masalan yozing:
"no text, no watermark, no extra fingers, no blur, low quality"

Natija: AI shu narsalardan qochadi — rasm toza chiqadi.

Qayerda ishlaydi: Krea, MidJourney va ko'p boshqa vositalarda.

Maslahat: agar rasmda doim bir xil xato chiqsa (masalan ortiqcha barmoq), uni negative promptga yozing.""",
    # для дня 20
    """📚 DARS: Aspect ratio — bitta prompt, turli o'lchamlar

Hurmatli do'stlar, bugun oxirgi dars — o'lcham (aspect ratio).

Bitta prompt, lekin turli joy uchun turli o'lcham kerak:
✅ 1:1 — Instagram post (kvadrat)
✅ 9:16 — Reels, Stories, TikTok (vertikal)
✅ 16:9 — YouTube, banner, prezentatsiya (gorizontal)

Nima uchun muhim:
Agar o'lchamni noto'g'ri tanlasangiz — rasm kesiladi yoki cho'ziladi. To'g'ri o'lcham = professional ko'rinish.

Maslahat: mijozga ish qilishdan oldin qayerga qo'yilishini so'rang, keyin o'lchamni tanlang.

Shu bilan mini-darslar tugadi. Chuqurroq bilim — oldinda!""",
]


# ============================================
# ПРОМПТЫ — 16 штук (вечер обычных дней)
# ============================================
PROMPT_POSTS = [
    """🎨 PROMPT: Kinematografik avatar (Nano Banana 2)

Ikkita rasm kerak: yuzingiz + referens uslub.

PROMPT (nusxa oling):
Use Image 1 as face reference (identity, features, skin tone). Use Image 2 as scene and lighting reference. Replace the face in Image 2 with the person from Image 1, keep identity and natural skin texture, match lighting and color grading. Ultra-realistic, cinematic lighting, sharp focus, professional photography.

Yuz + referens yuklang, promptni qo'ying, generatsiya.""",

    """🍽 PROMPT: Restoran taomi (Nano Banana 2)

PROMPT (nusxa oling):
Professional food photography of [taom nomi], close-up macro shot, steam rising, glistening textures, golden warm side lighting, dark moody background, shallow depth of field, appetizing rich colors, food magazine style, ultra-detailed, photorealistic, no text.

[taom nomi] o'rniga yozing: osh, manti, lag'mon, somsa.
Menyu va reklama uchun zo'r.""",

    """👗 PROMPT: Kiyim brendi videosi (Kling 3.0)

PROMPT (nusxa oling):
Fashion editorial video, model wearing an elegant outfit, walking confidently through an urban street, golden hour light, slow motion 60fps, cinematic tracking shot, fabric moving naturally, Instagram color grade, 4K, 10 seconds.

Kiyim rasmini yuklang, image-to-video, HD.
Kichik do'kon ham katta brend kabi reklama qiladi.""",

    """🚗 PROMPT: Avtomobil reklamasi (Nano Banana 2)

PROMPT (nusxa oling):
Cinematic car advertising shot, [mashina modeli/rangi], parked on a wet city street at night, neon reflections on the body, dramatic rim lighting, low angle, ultra-glossy paint, sharp reflections, professional automotive photography, ultra-realistic, high detail.

Avto-salon va e'lonlar uchun.""",

    """💍 PROMPT: Zargarlik / aksessuar (Nano Banana 2)

PROMPT (nusxa oling):
Luxury jewelry product photography, a gold ring on a soft silk surface, macro close-up, sparkling diamond, soft studio lighting with gentle reflections, elegant dark background, ultra-sharp focus, premium advertising look, photorealistic, high detail.

Zargarlik do'konlari uchun premium ko'rinish.""",

    """🏠 PROMPT: Kvartira interyeri (ko'chmas mulk)

PROMPT (nusxa oling):
Professional real-estate interior photography, modern bright living room, natural daylight through large windows, wide-angle 16mm, clean minimal design, soft shadows, realistic materials, warm cozy atmosphere, high detail, photorealistic, no people.

Ijara va sotuv e'lonlari uchun.""",

    """🔷 PROMPT: Logotip / emblema

PROMPT (nusxa oling):
Minimalist modern logo, [biznes sohasi], clean flat vector style, simple geometric emblem, balanced composition, 2-3 color palette, professional, on a transparent background, high quality, no extra text.

Matnni keyin Canva'da qo'shing — shunda toza chiqadi.""",

    """💄 PROMPT: Kosmetika mahsuloti (Nano Banana 2)

PROMPT (nusxa oling):
Cosmetic product photography, a cream jar on a marble surface with soft petals around, gentle diffused lighting, pastel tones, elegant minimal composition, water droplets for freshness, premium beauty-brand style, ultra-detailed, photorealistic.

Kosmetika va parvarish brendlari uchun.""",

    """☕ PROMPT: Kofe / kafe kadri (Nano Banana 2)

PROMPT (nusxa oling):
Cozy coffee shop photography, a latte with latte art on a wooden table, warm morning sunlight, shallow depth of field, steam rising, blurred cafe background, inviting atmosphere, photorealistic, high detail.

Kafe va restoranlar uchun ajoyib kontent.""",

    """🛍 PROMPT: E-commerce oq fon mahsulot

PROMPT (nusxa oling):
Clean e-commerce product photo, [mahsulot], centered on a pure white seamless background, even soft studio lighting, no shadows, sharp focus, true colors, catalog style, ultra-detailed, photorealistic.

Onlayn do'kon va marketplace (Uzum, Yandex) uchun.""",

    """👕 PROMPT: Logo mockup (futbolka / kружка)

PROMPT (nusxa oling):
Realistic product mockup, a plain t-shirt on a neutral studio background, soft even lighting, empty flat surface ready for a logo, sharp focus, true colors, professional mockup style, photorealistic.

Logoni keyin ustiga qo'ying — mijozga ko'rsatish uchun zo'r.""",

    """🎞 PROMPT: Retro / vintage portret (Nano Banana 2)

PROMPT (nusxa oling):
Vintage 90s film portrait, warm faded tones, soft grain, natural window light, nostalgic mood, analog film aesthetic, slightly desaturated colors, authentic retro look, photorealistic skin texture.

Instagram estetikasi uchun trend uslub.""",

    """🔍 PROMPT: Mahsulot makro detali (Nano Banana 2)

PROMPT (nusxa oling):
Extreme macro product shot, close-up on the texture and material detail of [mahsulot], dramatic directional lighting, crisp micro-detail, shallow depth of field, premium advertising style, ultra-realistic, high resolution.

Sifatni ko'rsatuvchi reklama uchun.""",

    """🏞 PROMPT: Turizm / manzara (sayohat biznesi)

PROMPT (nusxa oling):
Breathtaking travel photography, [joy nomi], golden hour, dramatic sky, vibrant natural colors, wide cinematic composition, crisp detail, professional landscape photography, ultra-realistic, high resolution.

Sayohat agentliklari va bloglar uchun.""",

    """📢 PROMPT: Poster / afisha foni (Nano Banana 2)

PROMPT (nusxa oling):
Modern event poster background, bold vibrant gradient, dynamic abstract shapes, clean composition with empty space for text, professional graphic-design style, high resolution, eye-catching.

Matnni Canva'da ustiga yozing.""",

    """📸 PROMPT: Instagram lifestyle foto (Nano Banana 2)

PROMPT (nusxa oling):
Aesthetic lifestyle photo, a person sitting in a stylish minimalist cafe, soft natural light, muted warm color grade, candid pose, shallow depth of field, trendy Instagram aesthetic, ultra-realistic, editorial finish.

Blogerlar va shaxsiy brend uchun.""",
]


# ============================================
# БЕСПЛАТНЫЕ РЕСУРСЫ — 4 штуки (вечер дней 5/10/15/20)
# В каждом — оговорка про меняющиеся лимиты.
# ============================================
FREE_LIMIT_NOTE = "\n\n⚠️ Bepul limitlar tez-tez o'zgaradi — bugun bor, ertaga kamayishi mumkin. Aniq holatni saytda tekshiring."

FREE_RESOURCE_POSTS = [
    # день 5
    """🆓 BEPUL rasm yaratish vositalari

Hurmatli do'stlar, rasm yasash uchun pul shart emas. Mana bepul boshlash mumkin bo'lganlar:

✅ Google Gemini — bepul, sifatli, kunlik limit bilan
✅ Leonardo.ai — har kuni bepul kredit beradi
✅ Krea — kunlik bepul kredit, karta shart emas
✅ Canva — bepul AI-vositalar (matn-rasm, fon olib tashlash)

Maslahat: bittadan boshlang, qaysi biri yoqishini sinang.""" + FREE_LIMIT_NOTE,

    # день 10
    """🆓 BEPUL video yaratish modellari

Hurmatli do'stlar, AI-video ham bepul sinash mumkin:

✅ Kling — har kuni bepul kredit (bir necha qisqa video uchun)
✅ Hailuo — kunlik bepul generatsiyalar
✅ Luma Dream Machine — oyiga bepul kredit

Diqqat: bepul tariflarda ko'pincha suv belgisi (watermark) bo'ladi, tijorat uchun pullik tarif kerak.""" + FREE_LIMIT_NOTE,

    # день 15
    """🆓 BEPUL foto yaxshilash (upscale) vositalari

Hurmatli do'stlar, xira yoki eski rasmni bepul tiniq qilish mumkin:

✅ Krea — upscale bo'limi, kunlik bepul kredit bilan
✅ Canva — rasm sifatini oshirish vositalari
✅ remove.bg — fonni bir zumda olib tashlash (bepul)

Kimga kerak: do'kon, ko'chmas mulk, eski oilaviy suratlar.""" + FREE_LIMIT_NOTE,

    # день 20
    """🆓 BEPUL AI-yordamchilar (matn, g'oya, tarjima)

Hurmatli do'stlar, kundalik ish uchun bepul yordamchilar:

✅ ChatGPT — bepul versiya, kunlik ish uchun yetadi
✅ Claude — uzun matn va tahlil uchun kuchli
✅ Google Gemini — bepul, katta kontekst bilan
✅ Perplexity — manba bilan qidiruv va tadqiqot uchun

Maslahat: bittasini tanlab, chuqur o'rganing — shunda tezroq natija.""" + FREE_LIMIT_NOTE,
]


# ============================================
# UNSPLASH
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
# ВЫБОР ПОСТА ПО ДНЮ ЦИКЛА
# ============================================
def pick_morning(day: int) -> str:
    """Утро: обучение в дни 5/10/15/20, иначе новость."""
    if day in LESSON_DAYS:
        # день 5->0, 10->1, 15->2, 20->3
        idx = sorted(LESSON_DAYS).index(day)
        return LESSON_POSTS[idx]
    # обычные дни -> новости по порядку (пропуская дни-уроки)
    normal_days = [d for d in range(1, CYCLE_DAYS + 1) if d not in LESSON_DAYS]
    idx = normal_days.index(day) % len(NEWS_POSTS)
    return NEWS_POSTS[idx]


def pick_evening(day: int) -> str:
    """Вечер: бесплатные ресурсы в дни 5/10/15/20, иначе промпт."""
    if day in LESSON_DAYS:
        idx = sorted(LESSON_DAYS).index(day)
        return FREE_RESOURCE_POSTS[idx]
    normal_days = [d for d in range(1, CYCLE_DAYS + 1) if d not in LESSON_DAYS]
    idx = normal_days.index(day) % len(PROMPT_POSTS)
    return PROMPT_POSTS[idx]


# ============================================
# ПУБЛИКАЦИЯ
# ============================================
async def publish(post_text: str):
    full_text = post_text + get_cta() + "\n\n" + get_hashtags()
    try:
        if len(full_text) <= TELEGRAM_CAPTION_LIMIT:
            image_url = get_image_url()
            if image_url:
                await bot.send_photo(chat_id=CHANNEL_USERNAME, photo=image_url, caption=full_text)
                logger.info("Опубликовано с картинкой (%s симв.)", len(full_text))
                return
        await bot.send_message(chat_id=CHANNEL_USERNAME, text=full_text, disable_web_page_preview=False)
        logger.info("Опубликовано текстом (%s симв.)", len(full_text))
    except Exception as e:
        logger.error("Ошибка публикации: %s", e)


async def publish_morning():
    day = cycle_day()
    logger.info("📰 Утро, день цикла %s", day)
    await publish(pick_morning(day))


async def publish_evening():
    day = cycle_day()
    logger.info("🎨 Вечер, день цикла %s", day)
    await publish(pick_evening(day))


async def keep_alive_ping():
    tz = timezone(timedelta(hours=5))
    logger.info("💚 Keep-alive — Ташкент %s", datetime.now(tz).strftime("%H:%M"))


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
    scheduler.add_job(keep_alive_ping, IntervalTrigger(minutes=10), id="keep_alive", replace_existing=True)
    scheduler.start()

    logger.info("🚀 Бот v5.0 запущен. Сегодня день цикла %s", cycle_day())
    logger.info("📅 10:00 (утро) и 19:00 (вечер), дни 5/10/15/20 — обучение + бесплатные ресурсы")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
