"""
Telegram-бот для автоматических постов в канал @AiContentCreatorUZ
Публикует пост раз в день на узбекском языке.
"""

import os
import random
import logging
from datetime import datetime
import requests
from telegram import Bot
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
from anthropic import Anthropic

# ============================================
# НАСТРОЙКИ — здесь меняй свои данные
# ============================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8648486286:AAFz9jI1xFZn4Sal9Khu9Yr_sVJb9qqoDqU")
CHANNEL_USERNAME = "@AiContentCreatorUZ"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # вставишь свой ключ
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")  # бесплатный, регистрация на unsplash.com/developers

# Время публикации (Ташкент UTC+5)
POST_HOUR = 10
POST_MINUTE = 0

# ============================================
# ЛОГИРОВАНИЕ
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# ТИПЫ ПОСТОВ ПО ДНЯМ НЕДЕЛИ
# ============================================

POST_TYPES = {
    0: "prompt",      # Понедельник — промпт для AI
    1: "news",        # Вторник — новость из мира AI
    2: "prompt",      # Среда — промпт
    3: "tip",         # Четверг — совет/лайфхак
    4: "prompt",      # Пятница — промпт
    5: "case",        # Суббота — кейс/история
    6: "motivation",  # Воскресенье — мотивация
}

# Темы для поиска картинок на Unsplash
IMAGE_THEMES = {
    "prompt": ["artificial intelligence", "creative design", "futuristic"],
    "news": ["technology", "innovation", "digital"],
    "tip": ["business", "marketing", "creative work"],
    "case": ["success", "advertising", "branding"],
    "motivation": ["success", "creative", "inspiration"],
}

# ============================================
# ГЕНЕРАЦИЯ ТЕКСТА ПОСТА (через Claude API)
# ============================================

def generate_post(post_type: str) -> str:
    """Генерирует текст поста на узбекском через Claude API."""
    
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    prompts = {
        "prompt": """Sen AI-kontent ishlab chiqaruvchi mutaxassissan. 
O'zbek tilida Telegram kanal uchun post yoz: brendlar uchun reklama yaratishda foydali Midjourney yoki Seedance promptini ulash.
Post strukturasi:
- Qiziqarli sarlavha (emoji bilan)
- Qisqa kirish (1-2 gap): qachon bu prompt ishlaydi
- Promptning o'zi (ingliz tilida, kod bloki sifatida)
- Maslahat: qanday qilib o'zgartirish mumkin
- 3-4 hashtag oxirida
Maksimum 800 belgi. Tabiiy, do'stona ohang.""",
        
        "news": """Sen AI-sohada ishlovchi mutaxassissan.
O'zbek tilida Telegram kanal uchun post yoz: AI-soha haqidagi qiziqarli yangilik yoki tendentsiya haqida.
Post strukturasi:
- Diqqatni jalb qiluvchi sarlavha (emoji bilan)
- Yangilikning mohiyati (2-3 gap)
- Bu nima uchun muhim biznes uchun
- Sening fikring yoki maslahating
- 3-4 hashtag
Maksimum 700 belgi. Aniq fakt yoki misol keltir.""",
        
        "tip": """Sen AI-kontent va reklama ishlab chiqaruvchi mutaxassissan.
O'zbek tilida Telegram kanal uchun foydali maslahat posti yoz: brendlar uchun AI-video yaratishda yo'l qo'yiladigan xatoliklar yoki yutuqli usullar haqida.
Post strukturasi:
- Sarlavha (emoji bilan)
- Muammo yoki vaziyat
- 3 ta aniq maslahat (raqamlangan)
- Yakuniy fikr
- 3-4 hashtag
Maksimum 800 belgi.""",
        
        "case": """Sen AI-kontent ishlab chiqaruvchisan.
O'zbek tilida Telegram kanal uchun keys-post yoz: qanday qilib AI-video brendga yordam berdi (umumiy misol, real ism ishlatma).
Post strukturasi:
- Sarlavha (emoji bilan)
- Muammo: brend nimaga duch keldi
- Yechim: AI yordamida nima qilindi
- Natija: nima o'zgardi
- Xulosa
- 3-4 hashtag
Maksimum 900 belgi.""",
        
        "motivation": """Sen kreativ ishchi va AI-kontent ishlab chiqaruvchisan.
O'zbek tilida Telegram kanal uchun motivatsion post yoz: kreativ ish, AI bilan ijod, frilanserlik haqida.
Post strukturasi:
- Sarlavha (emoji bilan)
- Hayotiy fikr yoki kuzatish
- Asosiy g'oya (3-4 gap)
- Harakatga chaqiruv
- 2-3 hashtag
Maksimum 600 belgi. Iliq, samimiy ohang.""",
    }
    
    prompt = prompts.get(post_type, prompts["tip"])
    
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text


# ============================================
# ПОИСК КАРТИНКИ НА UNSPLASH
# ============================================

def get_image_url(post_type: str) -> str:
    """Получает URL картинки с Unsplash по теме поста."""
    
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
# ПУБЛИКАЦИЯ ПОСТА
# ============================================

async def publish_post():
    """Главная функция — генерирует и публикует пост."""
    
    try:
        # Определяем тип поста по дню недели
        weekday = datetime.now().weekday()
        post_type = POST_TYPES[weekday]
        logger.info(f"Тип поста сегодня: {post_type}")
        
        # Генерируем текст
        text = generate_post(post_type)
        logger.info(f"Текст сгенерирован, {len(text)} символов")
        
        # Получаем картинку
        image_url = get_image_url(post_type)
        
        # Публикуем
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
        
        logger.info("✅ Пост опубликован успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка публикации: {e}")


# ============================================
# ЗАПУСК ПЛАНИРОВЩИКА
# ============================================

async def main():
    """Запускает бота с расписанием."""
    
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    
    # Каждый день в указанное время
    scheduler.add_job(
        publish_post,
        CronTrigger(hour=POST_HOUR, minute=POST_MINUTE),
        id="daily_post",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"🚀 Бот запущен. Посты будут публиковаться каждый день в {POST_HOUR}:{POST_MINUTE:02d} по Ташкенту")
    
    # Бот работает бесконечно
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
