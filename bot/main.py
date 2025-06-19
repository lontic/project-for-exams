import asyncio
from bot.handlers import setup_handlers
from bot.utils.config import load_config
from telegram.ext import Application


async def main():
    config = load_config()
    application = Application.builder().token(config.TELEGRAM_TOKEN).build()

    await setup_handlers(application)
    await application.initialize()
    await application.start()

    bot = await application.bot.get_me()
    print(f"Bot started as @{bot.username}")

    await application.updater.start_polling()
    await application.updater.idle()


if name == "main":
    asyncio.run(main())