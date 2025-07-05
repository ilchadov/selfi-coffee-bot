import logging
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
import os

# Настройки
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [237810136, 123456789, 987654321]  # замените на реальные ID админов

# Балансы пользователей (в памяти, можно заменить на базу данных)
balances = {}

# Кнопки
def get_main_keyboard(is_admin=False):
    buttons = [
        [InlineKeyboardButton("☕ Кофе", callback_data="coffee")],
        [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("💳 Пополнить", callback_data="recharge_info")]
    ]
    if is_admin:
        buttons += [
            [InlineKeyboardButton("📥 Пополнить кому-то", callback_data="admin_add")],
            [InlineKeyboardButton("📊 Таблица", callback_data="admin_table")],
            [InlineKeyboardButton("📉 Снять остатки", callback_data="admin_leftovers")],
            [InlineKeyboardButton("💸 Сбор дани", callback_data="admin_collect")]
        ]
    return InlineKeyboardMarkup(buttons)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    await update.message.reply_text(
        "Добро пожаловать в кофейного бота ☕",
        reply_markup=get_main_keyboard(is_admin)
    )

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    is_admin = user_id in ADMIN_IDS

    # Обработка
    if data == "coffee":
        balances[user_id] = balances.get(user_id, 0) - 50
        await query.edit_message_text(f"☕ Списано 50₽. Ваш баланс: {balances[user_id]}₽", reply_markup=get_main_keyboard(is_admin))
    elif data == "balance":
        await query.edit_message_text(f"💰 Ваш баланс: {balances.get(user_id, 0)}₽", reply_markup=get_main_keyboard(is_admin))
    elif data == "recharge_info":
        await query.edit_message_text("💳 Переведите нужную сумму на карту 1234 5678 9000 0000 и напишите администратору.")
    elif data == "admin_table":
        text = "\n".join([f"{uid}: {bal}₽" for uid, bal in balances.items()]) or "Нет данных"
        await query.edit_message_text(f"📊 Балансы:\n{text}")
    elif data == "admin_collect":
        for uid, bal in balances.items():
            if bal < 0:
                try:
                    await context.bot.send_message(uid, f"💸 У вас долг за кофе: {bal}₽. Пожалуйста, пополните баланс.")
                except Exception as e:
                    print(f"Ошибка при отправке: {e}")
        await query.edit_message_text("✅ Уведомления отправлены.")
    elif data == "admin_leftovers":
        count = sum(-bal // 50 for bal in balances.values() if bal < 0)
        await query.edit_message_text(f"📉 Остатки (долги): {count} чашек кофе")
    elif data == "admin_add":
        await query.edit_message_text("Пока не реализовано. Введите /admin_add ID сумма")

# Команда на ручное пополнение
async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
        balances[uid] = balances.get(uid, 0) + amount
        await update.message.reply_text(f"✅ Пополнено {amount}₽ для {uid}")
    except:
        await update.message.reply_text("❗️Использование: /admin_add ID СУММА")

# Неизвестные сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пожалуйста, используйте кнопки")

# Запуск
async def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin_add", admin_add))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
