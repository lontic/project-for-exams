from telegram.ext import CommandHandler
from bot.services.books import BookService


def setup_commands(application):
    book_service = BookService()

    command_handlers = [
        CommandHandler("start", book_service.start),
        CommandHandler("help", book_service.help_command),
        CommandHandler("recommend", book_service.recommend_command),
    ]

    for handler in command_handlers:
        application.add_handler(handler)