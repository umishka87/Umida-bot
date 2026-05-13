"""
Telegram-бот для канала @AiContentCreatorUZ
- 2 поста в день: 8:00 и 19:00 по Ташкенту
- Узбекский (латиница)
- Инсайдерский тон
- 6 видов CTA, чередуются
- Keep-alive пинг каждые 10 минут (защита от засыпания Railway)
- Тестовый пост при запуске
"""

import os
import random
import logging
from datetime import datetime, timezone, timedelta
import requests
from telegram import Bot
from telegram.constants import ParseMode
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

# Тестовая публикация при запуске (поставь False после первого успешного поста)
PUBLISH_ON_STARTUP = True

# ============================================
# ЛОГИРОВАНИЕ
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# РАСПИСАНИЕ ТЕМ
# ============================================

POST_SCHEDULE = {
    (0, "morning"): "news",
    (0, "evening"): "prompt_image",
    (1, "morning"): "insight",
    (1, "evening"): "lifehack",
    (2, "morning"): "news",
    (2, "evening"): "prompt_video",
    (3, "morning"): "agents",
    (3, "evening"): "automation",
    (4, "morning"): "news",
    (4, "evening"): "prompt_ads",
    (5, "morning"): "case",
    (5, "evening"): "weekend_lifehack",
    (6, "morning"): "easy_post",
    (6, "evening"): "tool_recommendation",
}

IMAGE_THEMES = {
    "news": ["technology", "innovation", "digital future"],
    "insight": ["business", "marketing", "industry"],
    "prompt_image": ["creative design", "art", "abstract"],
    "prompt_video": ["cinematic", "film production", "creative"],
    "prompt_ads": ["advertising", "branding", "luxury"],
    "lifehack": ["workspace", "productivity", "creative work"],
    "agents": ["artificial intelligence", "robot", "future tech"],
    "automation": ["network", "automation", "digital"],
    "case": ["success", "business growth", "achievement"],
    "weekend_lifehack": ["coffee", "lifestyle", "creative"],
    "easy_post": ["sunset", "calm", "minimalism"],
    "tool_recommendation": ["software", "tech tools", "modern"],
}

# ============================================
# CTA
# ============================================

CTA_LIST = [
    "\n\n📸 Mening barcha ishlarim Instagram'da: {ig}",
    "\n\n💼 Brendingiz uchun shunday video kerakmi? Umidaga yozing: {ig}",
    "\n\n🔥 Tez orada AI-video buyurtma berish haqida batafsil aytaman. Kanalga obuna bo'ling.",
    "\n\n💾 Postni saqlab qo'ying — kerak bo'ladi. Yangiliklarni o'tkazib yubormang.",
    "\n\n🚀 AI bilan ijod qilayotganlar uchun kanal — bu yerda eng yangi narsalarni topasiz.",
    "\n\n🎬 Umida brendlar uchun AI-reklamalar yaratadi. Instagram: {ig}",
]


def get_cta() -> str:
    cta = random.choice(CTA_LIST)
    return cta.format(ig=INSTAGRAM_USERNAME)


# ============================================
# ПРОМПТЫ
# ============================================

POST_PROMPTS = {
    "news": """Sen AI-soha bilan chuqur tanish odamsan. Kanalingda yangiliklarni do'stona, insayder ohangda yozasan.

Bugun yangilik posti yoz O'zbek tilida (LATIN harflarda).

Mavzu: AI-soha yangiligi yoki trendi.

OHANG: "Tasavvur qiling, endi shunday qilish mumkin..." yoki "Yangi narsa chiqdi..." — insayder ohang. EMAS o'qituvchi ohangda.

STRUKTURA:
- Sarlavha (1 emoji)
- Asosiy yangilik (2-3 gap)
- Nima uchun qiziq
- 2-3 hashtag

Maksimum 600 belgi. Faqat latin.""",

    "insight": """Sen AI va reklama sohasida insayder mutaxassissan.

Bugun insayt posti yoz O'zbek tilida (LATIN harflarda).

OHANG: "Sezganmisiz..." yoki "Qiziq narsa..." — kuzatuv tarzida.

STRUKTURA:
- Sarlavha
- Kuzatuv (3-4 gap)
- Xulosa
- 2-3 hashtag

Maksimum 600 belgi. Faqat latin.""",

    "prompt_image": """Sen AI-rasm generatsiyasi mutaxassisisan.

Midjourney yoki Flux uchun foydali prompt ulashuvchi post yoz O'zbek tilida (LATIN harflarda).

STRUKTURA:
- Sarlavha
- Prompt (ingliz tilida, kod blokida)
- Qachon ishlatish
- 2-3 hashtag

Maksimum 700 belgi. Faqat latin.""",

    "prompt_video": """Sen AI-video generatsiyasi mutaxassisisan.

Video uchun prompt ulashuvchi post yoz O'zbek tilida (LATIN harflarda).

STRUKTURA:
- Sarlavha
- Prompt (ingliz tilida, kod blokida)
- Tushuntirish
- 2-3 hashtag

Maksimum 700 belgi. Faqat latin.""",

    "prompt_ads": """Sen brendlar uchun AI-reklama mutaxassisisan.

Reklama uchun prompt ulashuvchi post yoz O'zbek tilida (LATIN harflarda).

STRUKTURA:
- Sarlavha
- Prompt (ingliz tilida, kod blokida)
- Qanday natija
- 2-3 hashtag

Maksimum 700 belgi. Faqat latin.""",

    "lifehack": """Sen AI-vositalar mutaxassisisan.

Lifhak posti yoz O'zbek tilida (LATIN harflarda).

OHANG: shaxsiy tajriba tarzida.

STRUKTURA:
- Sarlavha
- Vaziyat
- Lifhak
- Natija
- 2-3 hashtag

Maksimum 600 belgi. Faqat latin.""",

    "agents": """Sen AI va avtomatlashtirish mutaxassisisan.

AI-agentlar haqida post yoz O'zbek tilida (LATIN harflarda).

MUHIM: HALI o'zingni AI-bot deb tanitma.

STRUKTURA:
- Sarlavha
- AI-agent nima (oddiy)
- Biznesda nima qila oladi
- 2-3 hashtag

Maksimum 700 belgi. Faqat latin.""",

    "automation": """Sen biznes-avtomatlashtirish mutaxassisisan.

Avtomatlashtirish haqida post yoz O'zbek tilida (LATIN harflarda).

MUHIM: HALI o'zingni bot deb tanitma.

STRUKTURA:
- Sarlavha
- Muammo
- Yechim
- 2-3 hashtag

Maksimum 700 belgi. Faqat latin.""",

    "case": """Sen AI-kontent ishlab chiqaruvchisan.

Keys-post yoz O'zbek tilida (LATIN harflarda).

OHANG: hikoya tarzida.

STRUKTURA:
- Sarlavha
- Muammo
- Yechim
- Natija
- 2-3 hashtag

Maksimum 800 belgi. Faqat latin.""",

    "weekend_lifehack": """Yengil, ijodiy post yoz O'zbek tilida (LATIN harflarda).

OHANG: do'stona, dam olish kuni.

STRUKTURA:
- Sarlavha (yengil emoji)
- Asosiy fikr (3-4 gap)
- 2-3 hashtag

Maksimum 500 belgi. Faqat latin.""",

    "easy_post": """Yengil yakshanba posti yoz O'zbek tilida (LATIN harflarda).

OHANG: iliq, samimiy.

STRUKTURA:
- Sarlavha
- Fikr (2-3 gap)
- 2 hashtag

Maksimum 400 belgi. Faqat latin.""",

    "tool_recommendation": """AI-vosita haqida tavsiya posti yoz O'zbek tilida (LATIN harflarda).

OHANG: tavsiya tarzida.

STRUKTURA:
- Sarlavha
- Vosita nomi va nima qiladi
- Nima uchun foydali
- 2-3 hashtag

Maksimum 600 belgi. Faqat latin.""",
}


# ============================================
# ГЕНЕРАЦИЯ ТЕКСТА
# ============================================

def generate_post(post_type: str) -> str:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompt = POST_PROMPTS.get(post_type, POST_PROMPTS["news"])
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
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
# ТИП ПОСТА
# ============================================

def get_post_type(time_of_day: str) -> str:
    """Определяет тип поста на основе дня недели Ташкента."""
    tashkent_tz = timezone(timedelta(hours=5))
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
        
        if image_url:
            await bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=image_url,
                caption=text,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=text,
                parse_mode=ParseMode.MARKDOWN
            )
        
        logger.info("✅ Пост опубликован!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации: {e}")


async def publish_morning():
    await publish_post("morning")


async def publish_evening():
    await publish_post("evening")


# ============================================
# KEEP-ALIVE ПИНГ — защита от засыпания Railway
# ============================================

async def keep_alive_ping():
    """Каждые 10 минут пишет в логи что бот жив. Не даёт Railway усыпить."""
    tashkent_tz = timezone(timedelta(hours=5))
    current_time = datetime.now(tashkent_tz).strftime("%H:%M:%S")
    logger.info(f"💚 Keep-alive ping — бот активен. Ташкент: {current_time}")


# ============================================
# ЗАПУСК
# ============================================

async def main():
    # Тестовая публикация при запуске
    if PUBLISH_ON_STARTUP:
        logger.info("🧪 Тестовая публикация при запуске...")
        tashkent_tz = timezone(timedelta(hours=5))
        current_hour = datetime.now(tashkent_tz).hour
        time_of_day = "morning" if current_hour < 14 else "evening"
        await publish_post(time_of_day)
    
    # Регулярное расписание
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    # Утром 8:00
    scheduler.add_job(
        publish_morning,
        CronTrigger(hour=8, minute=0),
        id="morning_post",
        replace_existing=True
    )
    
    # Вечером 19:00
    scheduler.add_job(
        publish_evening,
        CronTrigger(hour=19, minute=0),
        id="evening_post",
        replace_existing=True
    )
    
    # Keep-alive каждые 10 минут (от засыпания Railway)
    scheduler.add_job(
        keep_alive_ping,
        IntervalTrigger(minutes=10),
        id="keep_alive",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("🚀 Бот запущен. Посты в 8:00 и 19:00 по Ташкенту. Keep-alive каждые 10 минут.")
    
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
