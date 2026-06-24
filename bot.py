"""
Telegram-бот для канала @AiContentCreatorUZ
ВЕРСИЯ 4.0 — на 10 дней с актуальным контентом

Изменения от 3.0:
- 20 постов на 10 дней (2 поста в день: 10:00 и 19:00 Ташкент)
- Контент основан на анализе @salikov_i и @podsobka_creatora
- Свежие AI-новости (MidJourney V8, Grok 4.3, Higgsfield Arena Zero, 
  Claude Mythos, Google Vids+Veo 3.1, и т.д.)
- Готовые промпты с переводом инструкций на узбекский
- Индексы постов сохраняются в файл (исправляет проблему повторов)
- Только РАБОЧИЕ узбекские хештеги
- Расписание: 10:00 и 19:00 Ташкент (5:00 и 14:00 UTC)
"""

import os
import json
import random
import logging
from datetime import datetime, timezone, timedelta
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

# Файл для сохранения индексов (исправляет повторы)
STATE_FILE = "/tmp/post_state.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================
# СОХРАНЕНИЕ ИНДЕКСОВ В ФАЙЛ
# ============================================

def load_state():
    """Загружает индексы из файла."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки state: {e}")
    return {"morning_index": 0, "evening_index": 0}


def save_state(state):
    """Сохраняет индексы в файл."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        logger.error(f"Ошибка сохранения state: {e}")


# ============================================
# ХЕШТЕГИ — ТОЛЬКО РАБОЧИЕ
# ============================================

HASHTAGS_MAIN = ["#uzbekistan", "#tashkent", "#toshkent", "#uzb", "#uzbek", "#uzbekiston", "#tashkentcity"]
HASHTAGS_REGIONS = ["#andijon", "#namangan", "#samarkand", "#buxoro", "#fargona"]
HASHTAGS_TELEGRAM = ["#telegram_yulduzlari", "#zortv", "#yulduzlari"]
HASHTAGS_CULTURE = ["#uzbekcha", "#uzbegim", "#uzbeks", "#uzbekistan_inst"]


def get_hashtags():
    """10 рабочих узбекских хештегов."""
    selected = []
    selected += random.sample(HASHTAGS_MAIN, 4)
    selected += random.sample(HASHTAGS_REGIONS, 2)
    selected += random.sample(HASHTAGS_TELEGRAM, 2)
    selected += random.sample(HASHTAGS_CULTURE, 2)
    return " ".join(selected)


# ============================================
# CTA
# ============================================

CTA_LIST = [
    f"\n\n📸 Mening ishlarim: {INSTAGRAM_URL}",
    f"\n\n💼 AI-video brendga kerakmi? {INSTAGRAM_URL}",
    f"\n\n🎬 AI-reklama: {INSTAGRAM_URL}",
    "\n\n🔥 Foydali bo'lsa — yurakcha bosing",
    "\n\n💾 Postni saqlab qo'ying",
    "\n\n💬 Savollar bormi? Sharhlarda yozing",
    "\n\n📤 Do'stingizga yuboring",
]


def get_cta():
    return random.choice(CTA_LIST)


# ============================================
# УТРЕННИЕ ПОСТЫ (10:00) — Новости и тренды
# ============================================

MORNING_POSTS = [
    # ===== ДЕНЬ 1 =====
    """🆕 MidJourney V8 chiqdi — sifat 4 marta oshdi

Hurmatli do'stlar, MidJourney V8 — keldi va bozorni o'zgartirdi.

Yangiliklar:

🎯 Native 2K rezolyutsiya (avval 1024px, endi 2048px)
📝 Matn yozish yaxshilandi — logotipdagi matn aniq chiqadi
🧠 Murakkab promptlarni tushunadi
🎨 "Chiroyli ammo qiyshiq" muammosi ketdi

V8 hozir Syntx agregatorida ham mavjud.

Kim uchun muhim:
✅ Dizaynerlar
✅ Brending uchun
✅ Posterlar va banner
✅ Mahsulot reklamasi

Reklama uchun MidJourney V8 + Kling video = eng kuchli juftlik 2026 yilda.""",

    # ===== ДЕНЬ 2 =====
    """🎬 Higgsfield AI-serial yaratdi — "Arena Zero"

Hurmatli do'stlar, Higgsfield Cinema Studio 2.5 da to'liq AI bilan yaratilgan serialning birinchi qismi chiqdi.

10 daqiqa sof AI:
✅ Personajlar — AI
✅ Sahnalar — AI
✅ Kamera harakati — AI
✅ Yorug'lik — AI
✅ Musiqa — AI

Nima anglatadi:

Hollywood'ga to'g'ridan-to'g'ri raqib. Kichik studiyalar endi Netflix darajasidagi kontent qila olishadi — million dollar byudjet kerak emas.

Real oqibatlar:
🎯 Reklama studiyalari qisqaradi
🎯 Aktyorlar AI bilan raqobat qiladi
🎯 Kichik kreatorlar katta loyihalar qila oladi
🎯 Kontent narxi 100 marta tushadi

Siz ham buni qila olasiz. Higgsfield obunasi $30/oydan.""",

    # ===== ДЕНЬ 3 =====
    """🆕 Grok 4.3 (Elon Musk'dan) — endi PDF va slaydlar

Hurmatli do'stlar, xAI yangi versiya chiqardi — Grok 4.3.

Nima yangi:

📄 PDF fayllar yaratadi
📊 Slaydlar (PowerPoint formatda)
📈 Jadvallar (Excel)
📝 Hujjatlar (Word)

Ya'ni:

Ilgari ChatGPT'da matn olib, keyin boshqa joyda PDF qilish kerak edi. Endi Grok hammasini o'zi qiladi.

Kim uchun foydali:
✅ Biznes — taqdimotlar tezroq
✅ O'qituvchilar — material tayyorlash
✅ Talabalar — kursovoy ishlar
✅ Marketinglar — hisobotlar

Qayerda: X Premium+ va SuperGrok obunalari orqali.

AI dunyosi har kuni yangilanadi. Charchamasdan, o'zingizga moslashtiring.""",

    # ===== ДЕНЬ 4 =====
    """🆕 Google Vids endi Veo 3.1 va Lyria 3 bilan ishlaydi

Hurmatli do'stlar, Google video-redaktor "Vids" ichiga kuchli AI qo'shildi.

Yangiliklar:

🎬 Veo 3.1 — video bevosita Vids ichida generatsiya
🎵 Lyria 3 — musiqa va ovoz uchun

Nima muhim:

✅ Endi bir dasturdan boshqasiga o'tish kerak emas
✅ Hammasi bir joyda — video, ovoz, musiqa
✅ Reklama agentliklari uchun katta tejov

Google bozorda Adobe va CapCut'ga to'g'ridan-to'g'ri raqobat boshlayapti. Bir necha oydan keyin Vids — asosiy raqib bo'ladi.

Bu kontent yaratuvchilar uchun ajoyib yangilik — yagona joyda hamma vositalar.""",

    # ===== ДЕНЬ 5 =====
    """🆕 Anthropic yangi Claude Mythos modelini ishlab chiqyapti

Hurmatli do'stlar, Anthropic rasman tasdiqladi — yangi model ustida ishlayapti.

Nima ma'lum:

🎯 Yangi nom — Claude Mythos
📊 Hozirgi Opus 4.6 dan kuchliroq
🔬 Yashirin sinov bosqichida
📝 Sirtga tashqari ish chiqdi — Anthropic 3000 ta loyiha hujjatini ko'chirib qo'ydi

Nima muhim:

Bu shuni anglatadi AI modellar shu darajada tez rivojlanyaptiki, hatto kompaniyalarning ichki ma'lumotlari endi anglashilmoqda.

Claude — kod yozish va matn ishi uchun eng yaxshilaridan. Mythos chiqsa, dasturlash va matnli ishlar yangi darajaga chiqadi.

Kuzatib boring. Yangiliklar tez chiqyapti.""",

    # ===== ДЕНЬ 6 =====
    """🆕 Adcreative.ai — reklama bannerlari uchun AI

Hurmatli do'stlar, yangi xizmat — Adcreative.ai.

Nima qila oladi:

🎨 Reklama banner generatsiya
✍️ Sotuvga moslangan matnlar
🎯 Sarlavhalar (headlines)
🖼️ Vizual uslublar tanlash
📊 To'liq reklama kampaniyalari

Bir necha soniyada — vaqtni katta tejaydi.

Kim uchun:
✅ Marketing direktorlari
✅ Kichik biznes egalari
✅ Instagram reklamasi qiluvchilar
✅ E-commerce do'konlar

Ilgari dizayner + marketolog kerak edi. Endi — bitta vosita hammasini qiladi.

AI har soha uchun yechim taklif qiladi. Endi reklama ham — sizning qo'lingizda.""",

    # ===== ДЕНЬ 7 =====
    """🆕 Google Gemini endi ChatGPT chatlarini import qiladi

Hurmatli do'stlar, Google katta yangilik qildi.

Nima yangi:

📥 Gemini'da yangi funksiya — boshqa AI-xizmatlardan chat va "xotirani" import qilish mumkin

Bu nima anglatadi:

Endi ChatGPT'dan Gemini'ga o'tsangiz — noldan boshlamasangiz mumkin. Eski chatlaringiz va modelning "tushunchasi" siz haqingizda — hammasi import qilinadi.

Nima muhim:

🎯 AI-xizmatlar orasida raqobat keskinlashdi
🎯 Foydalanuvchilar uchun erkinlik ortdi
🎯 Endi platforma almashtirish oson
🎯 Yashirib turgan ma'lumotlar — endi siz boshqarasiz

Bu Google'ning katta zarbasi ChatGPT'ga.

Qaysi AI'ni asosiy sifatida ishlatasiz? Sharhlarda yozing.""",

    # ===== ДЕНЬ 8 =====
    """🆕 Armenistanda $300 mln AI data-centr quriladi

Hurmatli do'stlar, MDH mintaqasida AI investitsiyalar tezlashyapti.

Armanistondagi yangilik:

💰 $300 mln — banklarning rekord krediti
🏢 Yangi AI data-centr quriladi
🤝 Nvidia va Dell hamkor

Bu nima anglatadi:

🎯 Mintaqada AI quvvati o'sayapti
🎯 Lokal AI-xizmatlar paydo bo'ladi
🎯 Ish o'rinlari — AI mutaxassislar uchun
🎯 Boshqa MDH davlatlari ham keladi

O'zbekiston'da AI:

Hozir bo'sh bozor. Birinchi bo'lganlar eng yaxshi joyni egallaydi. Bu sizning katta imkoniyatingiz.

Hozir o'rganing — keyin kech bo'ladi.

AI'da sizning maqsadingiz nima?""",

    # ===== ДЕНЬ 9 =====
    """📊 ChatGPT — haftada 800 mln foydalanuvchi

Hurmatli do'stlar, bu raqamga e'tibor bering.

ChatGPT statistikasi:

🌍 Haftada 800 mln aktiv foydalanuvchi
📈 Dunyo aholisining ~10%
⚡ Internet 7 yil kerak edi 100 mln'ga, ChatGPT — 2 oy

Bu tarix.

Tarixdagi eng tez tarqalgan texnologiya.

Nima anglatadi sizga:

🎯 AI endi "kelajak" emas — bugun
🎯 AI'siz ishlash — ortda qolish
🎯 AI'ni o'rganmoq — yangi savod (100 yil oldingi o'qish-yozish kabi)

Quyidagi savol o'zingizga bering:

Siz qancha vaqt AI bilan ishlaysiz?
- Har kuni?
- Haftada bir necha bor?
- Hech qachon?

Javob — sizning kelajagingiz.""",

    # ===== ДЕНЬ 10 =====
    """🚀 AI trendlari 2026 — nima muhim

Hurmatli do'stlar, bu yil AI dunyosida 10 ta katta trend.

Eng muhimlari:

1️⃣ Native ovoz va lablar
Veo va Kling endi to'liq ovozli video qiladi.

2️⃣ Uzun videolar
30-60 sekundli AI-video — endi standart.

3️⃣ Personaj consistency
Bir personaj — turli sahnalarda bir xil.

4️⃣ Multi-shot stories
Bitta promptdan butun hikoya.

5️⃣ 4K vertikal
TikTok va Reels uchun tayyor.

6️⃣ AI + real foto
Eng kuchli kombinatsiya — odam real, fon AI.

7️⃣ Avatarlar va gapiruvchi boshlar
HeyGen, Synthesia — yangi yo'nalish.

8️⃣ Open-source modellar
Bepul ishlash kompyuterda.

9️⃣ Real-time generation
2027 yilgacha — real vaqtda video.

🔟 AI'ga emas — tamoyillarga e'tibor
Yorug'lik, kompozitsiya, prompt strukturasi.

Trendlarni kuzating, lekin chuqurlikka boring.""",
]


# ============================================
# ВЕЧЕРНИЕ ПОСТЫ (19:00) — Промпты и психология
# ============================================

EVENING_POSTS = [
    # ===== ДЕНЬ 1 — ПРОМПТ Бойцовский клуб =====
    """🎨 PROMPT: Avatarka "Fight Club" uslubida

Hurmatli do'stlar, bugun beraman tayyor prompt — o'zingizga Brad Pitt uslubidagi avatar.

NIMA KERAK:
1. Sizning fotosurat (yuz aniq)
2. Brad Pitt fotosurati (Fight Club filmidan)
3. Nano Banana 2 — botda yoki saytda

PROMPT (nusxa olib joylashtiring):

Use Image 1 as face reference (identity, features, skin tone, hair). Use Image 2 as scene reference (lighting, pose, atmosphere). Replace face in Image 2 with person from Image 1. Keep identity, facial structure, skin tone, natural details from Image 1. Body should naturally match face — not simple face swap. Keep expression, camera angle, dramatic lighting from Image 2. Blend skin tones perfectly, match shadows and color grading. Keep background, clothing, environment identical to Image 2. Ultra-realistic, high detail, cinematic lighting, sharp focus, natural skin texture, professional photography.

QANDAY ISHLATISH:

1. Nano Banana 2 botiga kirish
2. Ikkita rasm yuklash (siz + referens)
3. Promptni qo'yish
4. 30 soniya kutish
5. Tayyor!

MASLAHAT: Referens rasm sifatli bo'lsin — yorug'lik aniq.""",

    # ===== ДЕНЬ 2 — ПРОМПТ Сюрреализм =====
    """🎨 PROMPT: Syurrealistik portret fashion uslubida

Hurmatli do'stlar, bugun beraman tayyor prompt — Vogue darajasidagi portret.

KONSEPT:

Bitta odam ikki versiyada. Kattalashtirilgan yuz sochlaridan ikkinchi versiya uchadi.

NIMA KERAK:
1. Sizning fotosurat
2. Nano Banana 2

PROMPT:

Create surreal high-fashion portrait with extreme scale distortion. Two versions of same person in frame. Foreground: massive upside-down close-up of face, dominating top-center. Head dramatically oversized. Looking down toward viewer, playful expression, natural skin texture. Background: full-length version of same person swinging from giant hair of foreground head, laughing, confident, wearing streetwear jacket. Environment: lush green meadow with tall wildflowers reaching into sky. Bright editorial lighting, crisp definition, rim light. Wide-angle lens 24-28mm effect, extreme foreground scale exaggeration. Mood: playful, bold, fashion-campaign energy. Vibrant tones, rich greens, magazine editorial finish. Ultra-realistic photography, high micro-detail, no CGI gloss.

QANDAY:
1. Nano Banana 2 ga kirish
2. Rasm yuklash
3. Promptni qo'yish
4. Generatsiya — 1-2 marta sinab ko'ring

Bu — Instagram portfeli uchun ajoyib!""",

    # ===== ДЕНЬ 3 — Психология одиночества =====
    """💬 "Hech kim meni tushunmaydi" — AI-kreator yolg'izligi

Hurmatli do'stlar, bu post juda shaxsiy. Lekin men bilaman — siz ham buni his qilasiz.

Qanday ko'rinish oladi:

🌙 Tunda kompyuterda o'tirasiz, promptlar yozasiz
🌙 Oilangiz: "Yana kompyuter? Boshqa ish yo'q?"
🌙 5 soat ishladingiz, lekin "rasm chizdim" deyish boladek ko'rinadi
🌙 O'sish ham g'alati ko'rinadi — "nimadir g'alati" deb baholanadi

Bu normalmi?

Mutlaqo. AI-kreator kasbi yangi. Yaqinlaringiz boshqa olamdadir.

Nima qilish kerak:

✅ Yaqinlardan tushunish kutmang
✅ Boshqa kreatorlar bilan ulashing
✅ Telegram guruhlari, YouTube — siz yolg'iz emassiz
✅ Faktlar bilan o'lchang ishingizni

Kuchli AI-kreatorlar yolg'izlikdan qutulmaydi — ular uni tushunadi va hamjamiyatga tayanadi.

Bu — kasbda yetuklik.""",

    # ===== ДЕНЬ 4 — ТОП-10 для Claude Code =====
    """🏆 Top-10 GitHub vositalar Claude Code uchun

Hurmatli do'stlar, agar Claude bilan kod yozasangiz, bu vositalar ishingizni 10x tezlashtiradi.

1. Claude Mem — doimiy xotira sessiyalar orasida
2. UI UX Pro Max — 50+ uslublar, 161 ranglar palitrasi
3. n8n-MCP — 400+ integratsiyalar
4. Everything Claude Code — to'liq agent harness
5. Awesome Claude Code — jamiyat tanlovi
6. Superpowers — strukturali fikrlash
7. Claude Code Ultimate Guide — 23K+ qator dokumentatsiya
8. Antigravity Awesome Skills — 1200+ tayyor ko'nikma
9. Claude Agent Blueprints — 75+ shablonlar
10. VoiceMode MCP — Claude bilan ovozli muloqot

Qayerda topish: github.com saytida har bir nom bo'yicha qidirish.

Bu vositalar — bepul. Ular jamiyat tomonidan yaratilgan.

Dasturlashni o'rganishni xohlaysizmi?

Claude Code — eng tezkor o'rganish yo'li. Til to'siq emas — ingliz bilim minimal kifoya.""",

    # ===== ДЕНЬ 5 — ПРОМПТ Kling 3.0 =====
    """🎬 PROMPT: Kinematografik portret Kling 3.0 da

Hurmatli do'stlar, bugun beraman prompt Kling 3.0 uchun — reklama darajasidagi natija.

NIMA KERAK:
1. Sizning yoki mahsulot rasmi
2. Kling 3.0 (kling.ai)

PROMPT:

Cinematic portrait shot, professional model, natural makeup, soft golden hour lighting, shallow depth of field, slow push-in camera movement, warm color grading, film grain texture, 4K quality, photorealistic, 8 seconds duration, smooth movement, natural facial expressions, subtle smile transitioning to confident look, eyes following light source, hair slightly moving in gentle breeze, background blurred warm bokeh, editorial fashion photography style.

QANDAY:
1. Kling.ai ga kirish (bepul 66 kredit/kun)
2. Image-to-video tanlash
3. Rasm yuklash
4. Promptni qo'yish
5. Sifat: HD yoki 4K
6. Davomiyligi: 5 yoki 10 sek
7. Generatsiya

NATIJA:

Reklama agentliklari ishlovchi sifat — bepul. Sosial tarmoqlar uchun, brending uchun, portfel uchun.

Kling 3.0 — №1 model 2026 yilda. Bepul tarif tijoriy ishlatish uchun emas.""",

    # ===== ДЕНЬ 6 — Совет 1+1+1 =====
    """💡 "1+1+1 qoidasi" — qanday vositalarni tanlash

Hurmatli do'stlar, ko'pchilik so'raydi: "10 ta model bor — qaysi birini tanlash?"

XATO YO'L: hammasini sinab ko'rish.
Bu sizni charchatadi va natija yo'q.

TO'G'RI YO'L: 1+1+1 qoidasi.

Tanlang:

🎨 1 ta model rasm uchun
(masalan: MidJourney yoki Flux yoki Nano Banana 2)

🎬 1 ta model video uchun
(masalan: Kling yoki Runway yoki Veo)

🧠 1 ta yordamchi matn uchun
(masalan: ChatGPT yoki Claude)

Va shu 3 ta vositada 3-6 oy ishlang. Chuqur o'rganing.

Nima uchun ishlaydi:

🎯 Tajriba — bir vositada 100 marta ishlash 10 ta vositada 1 martadan kuchliroq

🎯 Mijozlar tajribangizni payqaydilar — "shu narsani yaxshi qilaman" — ishonchli ovoz

🎯 Modellar o'zgaradi. Tamoyillar bir xil. Tamoyillarni o'rganing.

Yangi model chiqdi — sinab ko'ring 30 daqiqa. Yoqdimi? Davom eting. Yo'qmi? Eskingizga qayting.

AI marafondan, sprintdan emas.""",

    # ===== ДЕНЬ 7 — ПРОМПТ для еды =====
    """🍔 PROMPT: Restoran taom rasmi Nano Banana 2 da

Hurmatli do'stlar, restoranchilar va kafe egalari — bu siz uchun.

NIMA KERAK:
1. Taomning rasmi
2. Nano Banana 2

PROMPT:

Professional food photography of [your dish name], close-up macro shot, steam rising, glistening textures, natural ingredients visible, golden warm lighting from side, dark moody background, shallow depth of field, water droplets on fresh ingredients, appetizing colors, rich saturation, food magazine editorial style, photorealistic, ultra detailed textures, professional studio lighting, beautiful plating, garnishes visible, perfect composition, mouth-watering presentation.

[your dish name] o'rniga yozing: "lagman" yoki "plov" yoki "shashlik" — istalgan taom.

QANDAY:
1. Nano Banana 2 kirish
2. Taom rasmini yuklash
3. Promptni qo'yish
4. Generatsiya

NATIJA:

Instagram uchun professional rasmlar. Restoran reklamasi uchun zo'r. Fotograf yollashga $200-500 kerak — bu bepul.

Maslahat: "appetizing", "steaming hot", "fresh" so'zlari muhim — natija tabiiy bo'ladi.""",

    # ===== ДЕНЬ 8 — ПРОМПТ для одежды =====
    """👗 PROMPT: Kiyim brendingi uchun video Kling'da

Hurmatli do'stlar, kiyim do'koni egalari — bu siz uchun.

NIMA KERAK:
1. Kiyim katalog rasmi (oddiy)
2. Kling 3.0

PROMPT:

Fashion editorial video, beautiful model wearing elegant outfit, walking confidently through urban street, golden hour lighting, slow motion 60fps, cinematic camera following the model, soft wind moving the fabric naturally, vibrant city background slightly blurred, professional fashion photography style, model looking confidently at camera with subtle smile, hair flowing naturally, clothes moving with movement, color graded for Instagram aesthetic, 4K quality, smooth camera tracking shot, 10 seconds duration.

QANDAY:
1. Kling.ai kirish
2. Image-to-video tanlash
3. Kiyim rasmini yuklash
4. Promptni qo'yish
5. Sifat: HD
6. Davomiyligi: 10 sek

NATIJA:

Reklama agentligi darajasidagi video. Instagram uchun, TikTok uchun.

Ilgari: model, fotograf, studio, $500+. Endi: $0-5 (kreditda).

Kichik do'kon endi katta brand kabi reklama qila oladi.""",

    # ===== ДЕНЬ 9 — AI как новая грамотность =====
    """🧠 AI — yangi savod 2026 yilda

Hurmatli do'stlar, e'tibor bering bu fikrga.

100 yil oldin:
O'qish-yozishni bilmagan odam qul kabi ishlashga majbur edi.

50 yil oldin:
Kompyuter bilan ishlashni bilmagan — yaxshi ish topa olmadi.

Bugun:
AI bilan ishlashni bilmagan — ertaga ortda qoladi.

Bu juda jiddiy.

Quyidagi statistika:

📊 ChatGPT — haftada 800 mln foydalanuvchi
📊 Microsoft 6000 ishchini AI bilan almashtirdi
📊 Klarna 700 operatorni AI bilan almashtirdi ($40 mln tejam)
📊 2030 yilgacha 300 mln ish o'rni almashtiriladi

Nima qilish kerak:

✅ Kuniga 30 daqiqa AI bilan
✅ Bittasini chuqur o'rganing (ChatGPT yoki Claude)
✅ O'zingizning ishingizga moslang
✅ Bolaningizni ham o'rgating

5 yil ichida AI savoddan ortda qolish — kompyuter savodsizligiga teng bo'ladi.

Tanlov siz qo'lingizda.

Bugun boshlang. Erta kech bo'ladi.""",

    # ===== ДЕНЬ 10 — ПРОМПТ кинематографический портрет =====
    """🎥 PROMPT: Kinematografik portret Hollywood uslubida

Hurmatli do'stlar, yakuniy bonus — Hollywood uslubidagi portret.

NIMA KERAK:
1. Sizning fotosurat
2. Nano Banana 2

PROMPT:

Cinematic close-up portrait in Hollywood film style, professional lighting setup with key light from side, soft fill light, dramatic shadows on opposite side, shot on Arri Alexa camera, 85mm lens, shallow depth of field, photorealistic skin texture with natural pores visible, intense gaze, subtle expression, warm color grading reminiscent of Blade Runner 2049, atmospheric haze, slight film grain, professional cinematography, magazine editorial quality, sharp focus on eyes, hair detailed with light catching individual strands, neck and shoulders visible, blurred background with cinematic bokeh, ultra-realistic, no CGI gloss, natural human imperfections preserved, museum-quality portrait photography.

QANDAY:
1. Nano Banana 2 kirish
2. Rasm yuklash
3. Promptni qo'yish
4. Generatsiya
5. 2-3 marta sinab ko'ring — eng yaxshi natija tanlang

NATIJA:

LinkedIn uchun, sayt uchun, portfolio uchun — professional darajadagi portret.

Tovga jamiyatga ko'rinish — bu siz haqingizda birinchi taassurot.

10 dakka — 10 yillik tajribali fotograf darajasidagi natija.""",
]


# ============================================
# ПОЛУЧЕНИЕ КАРТИНКИ ЧЕРЕЗ UNSPLASH
# ============================================

IMAGE_QUERIES = ["ai technology", "artificial intelligence", "future tech", "neural network", "digital art", "creative ai"]


def get_image_url():
    if not UNSPLASH_ACCESS_KEY:
        return None
    
    query = random.choice(IMAGE_QUERIES)
    url = "https://api.unsplash.com/photos/random"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {"query": query, "orientation": "landscape"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()["urls"]["regular"]
    except Exception as e:
        logger.error(f"Ошибка картинки: {e}")
        return None


# ============================================
# ОБРЕЗКА ТЕКСТА
# ============================================

def trim_text(text: str, max_length: int = 1024) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[:max_length - 14]
    last_dot = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'), truncated.rfind('\n\n'))
    if last_dot > 500:
        return truncated[:last_dot + 1]
    return truncated[:truncated.rfind(' ')] + '.'


# ============================================
# ПУБЛИКАЦИЯ ПОСТА
# ============================================

async def publish_post(post_text: str):
    """Публикует пост в канал."""
    try:
        cta = get_cta()
        hashtags = "\n\n" + get_hashtags()
        full_text = post_text + cta + hashtags
        full_text = trim_text(full_text, 1024)
        
        image_url = get_image_url()
        bot = Bot(token=BOT_TOKEN)
        
        if image_url:
            await bot.send_photo(chat_id=CHANNEL_USERNAME, photo=image_url, caption=full_text)
        else:
            await bot.send_message(chat_id=CHANNEL_USERNAME, text=full_text)
        
        logger.info(f"✅ Опубликовано, длина: {len(full_text)}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации: {e}")


async def publish_morning():
    """10:00 Ташкент (5:00 UTC) — Утренний пост (новости)."""
    state = load_state()
    index = state["morning_index"] % len(MORNING_POSTS)
    
    post_text = MORNING_POSTS[index]
    logger.info(f"📰 Утренний пост #{index + 1}/{len(MORNING_POSTS)}")
    
    await publish_post(post_text)
    
    state["morning_index"] = index + 1
    save_state(state)


async def publish_evening():
    """19:00 Ташкент (14:00 UTC) — Вечерний пост (промпт/совет)."""
    state = load_state()
    index = state["evening_index"] % len(EVENING_POSTS)
    
    post_text = EVENING_POSTS[index]
    logger.info(f"🎨 Вечерний пост #{index + 1}/{len(EVENING_POSTS)}")
    
    await publish_post(post_text)
    
    state["evening_index"] = index + 1
    save_state(state)


# ============================================
# ОПРОСЫ — Пн/Ср/Пт в 20:00 Ташкент (15:00 UTC)
# ============================================

POLLS = [
    {"question": "Qaysi AI-rasm modelidan foydalanasiz? 🎨", "options": ["MidJourney", "Nano Banana 2", "Flux", "Hech qanday"]},
    {"question": "AI bilan kuniga qancha ishlaysiz? ⏰", "options": ["1 soatdan kam", "1-3 soat", "3-5 soat", "5+ soat"]},
    {"question": "Qaysi AI-video model qiziq? 🎬", "options": ["Kling 3.0", "Runway", "Veo 3.1", "Pika"]},
    {"question": "AI sizning ishingizni o'zgartirgan? 💼", "options": ["Ha, juda", "Ozgina", "Hozircha yo'q", "Sinab ko'rmoqdaman"]},
    {"question": "Yangi AI-vositalarni qanchalik kuzatasiz? 👀", "options": ["Har kuni", "Haftada bir", "Oyiga bir", "Tasodifan"]},
]


async def publish_poll():
    """Опросы Пн/Ср/Пт."""
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
        logger.info("🧪 Тестовая публикация...")
        await publish_morning()
    
    scheduler = AsyncIOScheduler(timezone="UTC")
    
    # 10:00 Ташкент = 5:00 UTC — Утренний пост (новости)
    scheduler.add_job(
        publish_morning,
        CronTrigger(hour=5, minute=0),
        id="morning_post",
        replace_existing=True
    )
    
    # 19:00 Ташкент = 14:00 UTC — Вечерний пост (промпты)
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
    logger.info("🚀 Бот v4.0 запущен")
    logger.info("📅 Расписание (Ташкент): 10:00 (новости) и 19:00 (промпты/советы)")
    logger.info(f"📰 Утренних постов: {len(MORNING_POSTS)}")
    logger.info(f"🎨 Вечерних постов: {len(EVENING_POSTS)}")
    
    state = load_state()
    logger.info(f"📊 State: morning={state['morning_index']}, evening={state['evening_index']}")
    
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
