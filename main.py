import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)
import os

# 🔐 Настройка токена
BOT_TOKEN = "7869918197:AAEgtYUzbrh7ILFmnafMwDSlJi3XBeaAMrk"

# 👑 ID администраторов
ADMIN_IDS = [237810136, 5649376616]  # @cramirezz и @vladislav_platitsyn

# 💰 Данные пользователей
user_balances = {}

# 🪪 Вспомогательная функция — проверить админа
def is_admin(user_id):
    return user_id in ADMIN_IDS

# 🏠 Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("☕ Кофе", callback_data="coffee")],
        [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📥 Пополнить", callback_data="recharge")],
    ]

    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👥 Пополнить другого", callback_data="admin_add")])
        keyboard.append([InlineKeyboardButton("📊 Таблица", callback_data="admin_table")])
        keyboard.append([InlineKeyboardButton("📉 Снять остатки", callback_data="admin_leftovers")])
        keyboard.append([InlineKeyboardButton("💸 Сбор дани", callback_data="admin_notify")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# 📩 Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or f"id{user_id}"

    if user_id not in user_balances:
        user_balances[user_id] = {"username": username, "balance": 0}

    action = query.data

    if action == "coffee":
        user_balances[user_id]["balance"] -= 50
        await query.edit_message_text(f"☕ Кофе списан — баланс: {user_balances[user_id]['balance']}₽")

    elif action == "balance":
        await query.edit_message_text(f"💰 Ваш баланс: {user_balances[user_id]['balance']}₽")

    elif action == "recharge":
        await query.edit_message_text("💳 Для пополнения переведите на карту: 2202 2036 0271 3023\nИ напишите админу.")

    elif action == "admin_add" and is_admin(user_id):
        buttons = [
            [InlineKeyboardButton(u["username"], callback_data=f"add_{uid}")]
            for uid, u in user_balances.items()
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Кому пополнить?", reply_markup=reply_markup)

    elif action.startswith("add_") and is_admin(user_id):
        target_id = int(action.split("_")[1])
        user_balances[target_id]["balance"] += 50
        await query.edit_message_text(
            f"✅ Пополнено 50₽ для {user_balances[target_id]['username']}. Новый баланс: {user_balances[target_id]['balance']}₽"
        )

    elif action == "admin_table" and is_admin(user_id):
        text = "📊 Таблица баланса:\n"
        for u in user_balances.values():
            text += f"@{u['username']}: {u['balance']}₽\n"
        await query.edit_message_text(text)

    elif action == "admin_leftovers" and is_admin(user_id):
        total_coffee = sum(
            abs(u["balance"] // 50) for u in user_balances.values() if u["balance"] < 0
        )
        await query.edit_message_text(f"☕ Неоплаченных кофе: {total_coffee} (зерно и молоко)")

    elif action == "admin_notify" and is_admin(user_id):
        for uid, u in user_balances.items():
            if u["balance"] < 0:
                try:
                    await context.bot.send_message(
                        chat_id=uid,
                        text=f"🔔 Привет, @{u['username']}! У тебя задолженность за кофе — {u['balance']}₽. Не забудь пополнить 🙏"
                    )
                except Exception as e:
                    print(f"Ошибка при отправке сообщения {u['username']}: {e}")
        await query.edit_message_text("✅ Уведомления отправлены.")

# 🧹 Обработка неизвестных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пожалуйста, используй кнопки ниже или /start")

# 🚀 Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()
    await app.start()
    print("Бот запущен...")
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
