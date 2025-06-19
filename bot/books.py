import asyncio
import logging
from typing import Optional, List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.repositories import BookRepository
from bot.services.ai import AIService
from bot.services.images import ImageService
from bot.utils.helpers import rate_limit
from bot.utils.config import Config

logger = logging.getLogger(__name__)


class BookService:
    def __init__(self, config: Config):
        self.config = config
        self.repository = BookRepository(config.DATABASE_NAME)
        self.ai_service = AIService(config)
        self.image_service = ImageService()

        # Константы для клавиатур
        self.MAIN_MENU_KEYBOARD = [
            [InlineKeyboardButton("📖 По жанрам", callback_data='genres')],
            [InlineKeyboardButton("✍️ По авторам", callback_data='authors')],
            [InlineKeyboardButton("💡 Рекомендации", callback_data='recommend')],
            [InlineKeyboardButton("🎨 Генерация изображений", callback_data='generate_image')],
            [InlineKeyboardButton("⭐ Избранное", callback_data='favorites')],
            [InlineKeyboardButton("📊 Статистика", callback_data='stats')]
        ]

        self.GENRES = [
            "Фэнтези", "Детектив", "Научная фантастика", "История",
            "Романтика", "Триллер", "Биография", "Поэзия"
        ]

        self.AUTHORS = [
            "Стивен Кинг", "Фёдор Достоевский", "Агата Кристи",
            "Джордж Оруэлл", "Дж. К. Роулинг", "Дж. Р. Толкин"
        ]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_message = (
            f"📚 Привет, {user.first_name}!\n\n"
            "Я - умный книжный бот, который поможет тебе:\n"
            "• Найти лучшие книги по любой теме\n"
            "• Получить персонализированные рекомендации\n"
            "• Сохранять понравившиеся книги\n\n"
            "Напиши тему книги или нажми /help для меню."
        )

        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help с инлайн-клавиатурой"""
        reply_markup = InlineKeyboardMarkup(self.MAIN_MENU_KEYBOARD)
        await update.message.reply_text("📚 Главное меню:", reply_markup=reply_markup)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показывает статистику пользователя"""
        user_id = update.effective_user.id
        stats = self.repository.get_user_stats(user_id)
        favorites_count = len(self.repository.get_user_favorites(user_id))

        message = (
            f"📊 Ваша статистика:\n\n"
            f"• Всего запросов: {stats['query_count']}\n"
            f"• Последняя активность: {stats['last_active']}\n"
            f"• Сохранённых книг: {favorites_count}\n\n"
            "Продолжайте открывать новые книги!"
        )

        await update.message.reply_text(message)

    async def recommend_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Генерирует персонализированные рекомендации"""
        user_id = update.effective_user.id
        past_queries = self.repository.get_user_queries(user_id, limit=5)

        if not past_queries:
            await update.message.reply_text("У вас ещё нет запросов для анализа интересов.")
            return

        prompt = " | ".join(past_queries)
        await update.message.reply_text(f"🔍 Анализирую ваши интересы: {prompt}...")

        try:
            response = await self.ai_service.generate_books_recommendation(prompt)
            await update.message.reply_text(response, parse_mode="Markdown")

            # Сохраняем запрос и ответ
            self.repository.save_query(user_id, prompt, response)
        except Exception as e:
            logger.error(f"Recommendation error: {e}")
            await update.message.reply_text("Произошла ошибка при генерации рекомендаций.")

    @rate_limit(5)
    async def handle_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает текстовые запросы на поиск книг"""
        user_id = update.effective_user.id
        query = update.message.text.strip()

        if len(query) > self.config.MAX_QUERY_LENGTH:
            await update.message.reply_text(
                f"Слишком длинный запрос. Максимум {self.config.MAX_QUERY_LENGTH} символов.")
            return

        await update.message.reply_text("🔍 Ищу подходящие книги...")

        try:
            # Проверяем кэш
            cached = self.repository.get_cached_response(query)
            if cached:
                await update.message.reply_text(cached, parse_mode="Markdown")
                return

            # Генерируем новый ответ
            response = await self.ai_service.generate_books_recommendation(query)
            await update.message.reply_text(response, parse_mode="Markdown")

            # Сохраняем в БД
            self.repository.save_query(user_id, query, response)
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("Произошла ошибка при поиске книг.")

    async def show_genres(self, update: Update) -> None:
        """Показывает клавиатуру с жанрами"""
        keyboard = [
            [InlineKeyboardButton(genre, callback_data=f"genre:{genre}")]
            for genre in self.GENRES
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])

        await update.callback_query.edit_message_text(
            "📚 Выберите жанр:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def show_authors(self, update: Update) -> None:
        """Показывает клавиатуру с авторами"""
        keyboard = [
            [InlineKeyboardButton(author, callback_data=f"author:{author}")]
            for author in self.AUTHORS
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])

        await update.callback_query.edit_message_text(
            "✍️ Выберите автора:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_genre_author_selection(self, update: Update, selection_type: str, value: str) -> None:
        """Обрабатывает выбор жанра или автора"""
        user_id = update.effective_user.id
        await update.callback_query.edit_message_text(f"🔍 Ищу книги {selection_type}: {value}...")

        try:
            response = await self.ai_service.generate_books_recommendation(value)
            self.repository.save_query(user_id, value, response)

            # Клавиатура с кнопкой "Добавить в избранное"
            keyboard = [
                [InlineKeyboardButton("⭐ Добавить в избранное", callback_data=f"add_fav:{value}")],
                [InlineKeyboardButton("🔙 Назад", callback_data=f"{selection_type}s")]
            ]

            await update.callback_query.message.reply_text(
                response,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Genre/author search error: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка при поиске.")

    async def show_favorites(self, update: Update) -> None:
        """Показывает избранные книги пользователя"""
        user_id = update.effective_user.id
        favorites = self.repository.get_user_favorites(user_id)

        if not favorites:
            await update.callback_query.edit_message_text("У вас пока нет сохранённых книг.")
            return

        # Создаем клавиатуру с книгами и кнопками удаления
        keyboard = [
            [
                InlineKeyboardButton(f"{i + 1}. {book['title'][:20]}...", callback_data=f"show_fav:{i}"),
                InlineKeyboardButton("❌", callback_data=f"del_fav:{book['title']}")
            ]
            for i, book in enumerate(favorites)
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='main_menu')])

        await update.callback_query.edit_message_text(
            "⭐ Ваши сохранённые книги:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def generate_book_image(self, update: Update) -> None:
        """Генерирует изображение по интересам пользователя"""
        user_id = update.effective_user.id
        past_queries = self.repository.get_user_queries(user_id, limit=3)

        if not past_queries:
            await update.callback_query.edit_message_text("У вас ещё нет запросов для генерации изображения.")
            return

        prompt = ", ".join(past_queries)
        await update.callback_query.edit_message_text(f"🎨 Генерирую изображение по вашим интересам...")

        try:
            image_url = await self.image_service.generate(prompt)
            if image_url:
                await update.callback_query.message.reply_photo(
                    photo=image_url,
                    caption="🖼 Ваше изображение по интересам",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Назад", callback_data='main_menu')]
                    ])
                )
            else:
                await update.callback_query.message.reply_text("Не удалось сгенерировать изображение.")
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            await update.callback_query.message.reply_text("Произошла ошибка при генерации изображения.")