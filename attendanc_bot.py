from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging
from datetime import datetime

API_TOKEN = '7393093433:AAFX-NwncfNOEZfEi_J20-ndhX7_LR1tP7E'
ADMIN_CHAT_ID = '1060424325'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Словарь для хранения состояния пользователей
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    keyboard = [
        [InlineKeyboardButton("Да", callback_data='present_yes')],
        [InlineKeyboardButton("Нет", callback_data='present_no')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f'Привет, {user.first_name}! Этот бот предназначен для проверки твоего присутствия. Ты сегодня будешь?', 
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    await query.answer()
    data = query.data

    if data == 'present_yes':
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Кто: @{user.username}\nКогда: {datetime.now()}\nПрисутствие: Да")
        await query.edit_message_text(text="Спасибо за ответ. Хорошего дня!")
    elif data == 'present_no':
        keyboard = [
            [InlineKeyboardButton("Целый день", callback_data='absent_fullday')],
            [InlineKeyboardButton("Часть дня", callback_data='absent_partday')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Целый день или часть дня?", reply_markup=reply_markup)
    elif data in ['absent_fullday', 'absent_partday']:
        user_states[query.from_user.id] = {
            'absence_duration': 'Целый день' if data == 'absent_fullday' else 'Часть дня',
            'awaiting_proof': True
        }
        await query.edit_message_text(text="Напиши, по какой причине тебя не будет, или пришли фотографию документа, подтверждающего твоё отсутствие.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in user_states:
        state = user_states[user_id]
        absence_duration = state.get('absence_duration')
        awaiting_proof = state.get('awaiting_proof')
        awaiting_documentation = state.get('awaiting_documentation')

        if awaiting_proof:
            text = update.message.text
            photo = update.message.photo

            if text:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Кто: @{update.message.from_user.username}\nКогда: {datetime.now()}\nПрисутствие: Нет\nПродолжительность: {absence_duration}\nДоказательство: {text}")
            elif photo:
                file_id = photo[-1].file_id
                file = await context.bot.get_file(file_id)
                file_path = await file.download_to_drive()
                await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=file_id, caption=f"Кто: @{update.message.from_user.username}\nКогда: {datetime.now()}\nПрисутствие: Нет\nПродолжительность: {absence_duration}\nДоказательство: Фото")

            await update.message.reply_text("Спасибо за ответы. Будем тебя ждать!")
            user_states.pop(user_id, None)  # Очистить состояние пользователя
        
        elif awaiting_documentation:
            text = update.message.text
            photo = update.message.photo

            if text:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Кто: @{update.message.from_user.username}\nКогда: {datetime.now()}\nДополнительно: {text}")
            elif photo:
                file_id = photo[-1].file_id
                file = await context.bot.get_file(file_id)
                file_path = await file.download_to_drive()
                await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=file_id, caption=f"Кто: @{update.message.from_user.username}\nКогда: {datetime.now()}\nДополнительно: Фото")

            await update.message.reply_text("Спасибо за ответ. Возвращайся поскорее!")
            user_states.pop(user_id, None)  # Очистить состояние пользователя
        
        else:
            await update.message.reply_text("Неизвестная команда. Пожалуйста, начни сначала, нажав /start.")

async def addition(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_states[user_id] = {'awaiting_documentation': True}
    await update.message.reply_text("Что-то случилось и ты не можешь присутствовать? Опиши здесь причину или пришли фото.")

def main() -> None:
    application = ApplicationBuilder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("addition", addition))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
