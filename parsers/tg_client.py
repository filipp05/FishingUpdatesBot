import os
import logging
import asyncio
import time
import re
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BotCommand
from aiogram.filters import Command
from parsers.js_parser import parse_jpsnasti

PRODUCT_NUM = 10  # Количество продуктов для сравнения
TIME_PERIOD = 300  # Интервал проверки в секундах
PRODUCTS_DISPLAY_NUM = 5  # Количество продуктов для отображения в сообщении

dp = Dispatcher()
logging.basicConfig(level=logging.INFO)
active_tasks = {}


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.reply(
        "Привет! Используй /parse для запуска мониторинга изменений."
    )


@dp.message(Command("stop"))
async def stop_handler(message: Message):
    chat_id = message.chat.id
    if chat_id in active_tasks:
        task = active_tasks[chat_id]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        del active_tasks[chat_id]
        await message.reply("🛑 Мониторинг остановлен.")
    else:
        await message.reply("ℹ️ Нет активного мониторинга для остановки.")


@dp.message(Command("parse"))
async def parse_handler(message: Message):
    chat_id = message.chat.id

    if chat_id in active_tasks:
        old_task = active_tasks[chat_id]
        old_task.cancel()
        try:
            await old_task
        except asyncio.CancelledError:
            pass
        del active_tasks[chat_id]

    # Создаем новую задачу мониторинга
    task = asyncio.create_task(monitor_changes(chat_id, message.bot))
    active_tasks[chat_id] = task

    await message.reply("🚀 Мониторинг запущен. Ожидайте уведомлений...")


async def monitor_changes(chat_id: int, bot: Bot):
    def prepare_for_comparison(products):
        return [
            {k: v for k, v in product.items() if k != 'image_url'}
            for product in products
        ]

    loop = asyncio.get_event_loop()
    try:
        prev_products = await loop.run_in_executor(None, parse_jpsnasti)
    except Exception as e:
        logging.error(f"Ошибка парсинга: {e}")
        await bot.send_message(chat_id, "❌ Ошибка при загрузке данных!")
        return

    prev_timestamp = time.time()
    prev_comp = prepare_for_comparison(prev_products)

    while True:
        await asyncio.sleep(TIME_PERIOD)

        try:
            temp_products = await loop.run_in_executor(None, parse_jpsnasti)
            temp_comp = prepare_for_comparison(temp_products)
        except Exception as e:
            logging.error(f"Ошибка парсинга: {e}")
            continue

        diffs = []
        for prod in temp_comp:
            if prod not in prev_comp:
                diffs.append(prod)

        if diffs:
            logging.info("Обнаружены изменения в продуктах:")
            for new in diffs:
                logging.info("Появился: %s", new)

            alert_products = [new for new in diffs][::PRODUCTS_DISPLAY_NUM]
            response = "🔔 **Обнаружены изменения!**\n\n"

            for product in alert_products:
                response += (
                    f"🏷 *{product['title']}*\n"
                )

            try:
                await bot.send_message(
                    chat_id,
                    response,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                prev_products = temp_products.copy()
                prev_comp = temp_comp.copy()
            except Exception as e:
                logging.error(f"Ошибка отправки: {e}")


@dp.message()
async def default_handler(message: Message):
    await message.reply("ℹ️ Используйте /parse для запуска мониторинга.")


class TGClient:
    def __init__(self):
        self.bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        if not self.bot.token:
            raise ValueError("Токен бота не найден!")

    async def start(self):
        await self.bot.set_my_commands([
            BotCommand(command="start", description="Старт"),
            BotCommand(command="parse", description="Запустить мониторинг"),
        ])
        await dp.start_polling(self.bot)


if __name__ == "__main__":
    client = TGClient()
    asyncio.run(client.start())
