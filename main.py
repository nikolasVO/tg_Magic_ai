# main.py

from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters
from natal_chart import start_natal_chart, get_date, get_time, get_place, process_confirmation, cancel, DATE, TIME, PLACE, CONFIRMATION
import config  # Импортируем модуль config

async def start(update, context):
    welcome_message = (
        "Привет! Выбери один из пунктов:\n"
        "🔮 Натальная астрология /natal_chart\n"
        # Добавьте остальные разделы по мере необходимости
    )
    await update.message.reply_text(welcome_message)

def main():
    TOKEN = config.TOKEN  # Получаем токен из config.py

    if not TOKEN:
        print("Ошибка: Токен бота не установлен. Пожалуйста, установите его в файле config.py.")
        return

    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('menu', start))  # Добавили команду /menu

    # Обработчик для /natal_chart
    natal_chart_conv = ConversationHandler(
        entry_points=[CommandHandler('natal_chart', start_natal_chart)],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_place)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(natal_chart_conv)

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
