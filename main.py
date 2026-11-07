
import asyncio
import json
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import BusinessConnection, Message

TOKEN = "ВАШ_ТОКЕН_БОТА"
DB_FILE = Path("connections.json")

bot = Bot(TOKEN)
dp = Dispatcher()

# ---------- Хранилище connection_id ----------
def load_connections() -> dict:
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {}

def save_connections(data: dict):
    DB_FILE.write_text(json.dumps(data))

# ---------- Шаг 1: Сохраняем ID подключения при добавлении бота ----------
@dp.business_connection()
async def on_business_connection(connection: BusinessConnection):
    data = load_connections()
    data[str(connection.user.id)] = connection.id
    save_connections(data)
    print(f"Business connection saved: {connection.id}")

# ---------- Шаг 2: Обработка команды /offer в Business-чате ----------
@dp.business_message(F.text.startswith("/offer"))
async def handle_offer(message: Message):
    # Получаем connection_id из сохранённого хранилища
    data = load_connections()
    connection_id = data.get(str(message.from_user.id))

    if not connection_id:
        await message.answer("❌ Бот не подключён к Business-аккаунту. Добавьте его в настройках Telegram Business.")
        return

    parts = message.text.strip().split()
    if len(parts) < 4:
        await message.answer(
            "❌ Формат: /offer <chat_id> <ссылка_на_nft> <сумма> [валюта] [язык]\n"
            "Пример: /offer 123456789 https://t.me/nft/SnoopDogg-9545 150 GRAM eng"
        )
        return

    chat_id_raw = parts[1]
    nft_link = parts[2]
    amount = parts[3]
    currency = parts[4].upper() if len(parts) > 4 else "STARS"
    lang = parts[5].upper() if len(parts) > 5 else "RU"

    # ---------- Валидация ----------
    if not chat_id_raw.lstrip("-").isdigit():
        await message.answer("❌ chat_id должен быть числом.")
        return

    if not re.fullmatch(r"https://t\.me/nft/[\w\-]+", nft_link):
        await message.answer("❌ Ссылка должна быть вида: https://t.me/nft/...")
        return

    if currency not in ("STARS", "GRAM"):
        await message.answer("❌ Валюта: STARS или GRAM.")
        return

    if lang not in ("RU", "EN"):
        await message.answer("❌ Язык: RU или EN.")
        return

    # ---------- Формирование текста предложения ----------
    if lang == "RU":
        offer_text = (
            "📖 Предложение о покупке подарка\n\n"
            f"🎁 Подарок: {nft_link}\n"
            f"💰 Сумма: {amount} {currency}\n\n"
            "Если согласны — ответьте на это сообщение."
        )
    else:
        offer_text = (
            "📖 Gift purchase offer\n\n"
            f"🎁 Gift: {nft_link}\n"
            f"💰 Amount: {amount} {currency}\n\n"
            "Reply to this message if you agree."
        )

    # ---------- Отправка от имени вашего аккаунта ----------
    try:
        await bot.send_message(
            chat_id=int(chat_id_raw),
            text=offer_text,
            business_connection_id=connection_id,
        )
        await message.answer(
            f"✅ Оффер отправлен в {chat_id_raw}\n"
            f"Сумма: {amount} {currency}\n"
            f"Язык: {lang}"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")

# ---------- Запуск ----------
async def main():
    print("Бот запущен. Ожидание команд...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
