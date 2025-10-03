import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from app.config import config
from app.database import db
from app.game_menus import GameMenus, TextTemplates
from app.game_manager import GameManager
from app.hand_analyzer import hand_analyzer, history_analyzer
from app.history_manager import history_manager
from app.statistics import stats_manager
from app.ml.model_trainer import model_trainer

# В начале файла добавьте:
from app.poker_engine import Card, Rank, Suit
from app.game_menus import AnalysisMenus

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PokerMentorBot:
    """Главный класс бота - конструктор функциональности"""
    
    def __init__(self):
        # Проверяем конфигурацию
        is_valid, message = config.validate()
        if not is_valid:
            logger.error(f"Конфигурация невалидна: {message}")
            raise ValueError(message)
        
        # Инициализируем базу данных
        db.init_db()
        
        # Инициализируем менеджер игр
        self.game_manager = GameManager()
        
        # Создаем приложение Telegram
        self.token = config.get('TELEGRAM_BOT_TOKEN')
        self.application = Application.builder().token(self.token).build()
        
        # Настраиваем обработчики
        self._setup_handlers()
        logger.info("Poker Mentor Bot инициализирован")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд - конструктор функциональности"""
        # Команды
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("settings", self._handle_settings))

        self.application.add_handler(CommandHandler("test_game", self._handle_test_game))
        self.application.add_handler(CommandHandler("choose_ai", self._handle_choose_ai))

        self.application.add_handler(CommandHandler("analyze", self._handle_analyze))  # ← ДОБАВЬ ЭТУ СТРОКУ
        self.application.add_handler(CommandHandler("debug", self._handle_debug))

        self.application.add_handler(CommandHandler("history", self._handle_history))
        self.application.add_handler(CommandHandler("stats", self._handle_stats))

        self.application.add_handler(CommandHandler("ml_status", self._handle_ml_status))
        self.application.add_handler(CommandHandler("train_ml", self._handle_train_ml))
        # Обработчики кнопок и сообщений
        self.application.add_handler(CallbackQueryHandler(self._handle_callback_query))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
    
    # ===== ОСНОВНЫЕ ОБРАБОТЧИКИ =====
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Сохраняем пользователя в БД
        db_user = db.add_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Получаем статистику
        user_stats = db.get_user_stats(db_user['id'])
        hands_played = user_stats['total_hands_played'] if user_stats else 0
        
        # Отправляем приветствие
        welcome_text = TextTemplates.get_welcome_text(
            user.first_name, db_user['level'], hands_played
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=GameMenus.get_main_menu()
        )
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        await update.message.reply_text(TextTemplates.get_help_text())
    
    async def _handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        await update.message.reply_text(
            "⚙️ Текущие настройки:\n"
            f"• Версия: 1.0\n"
            f"• База данных: {config.get('DATABASE_URL', 'Не настроена')}\n"
            f"• Ставки: {config.get('DEFAULT_STAKE', '1/2')}\n\n"
            "Для изменения настроек отредактируйте файл config.txt"
        )
    
    async def _handle_test_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /test_game"""
        user_id = str(update.effective_user.id)
        
        # Создаем тестовую игру
        game = self.game_manager.create_game(user_id, "fish")
        game_state = self.game_manager.get_game_state(user_id)
        
        # Отправляем информацию о игре
        game_text = TextTemplates.get_game_start_text(
            "Fish", 
            GameMenus.get_ai_description("fish"),
            game_state["user_cards"],
            game_state["user_stack"],
            game_state["pot"]
        )
        
        await update.message.reply_text(game_text)
        await self._show_game_actions(update, context, user_id)
    
    async def _handle_choose_ai(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /choose_ai"""
        await update.message.reply_text(
            "🤖 Выберите тип AI оппонента:",
            reply_markup=GameMenus.get_ai_selection_menu()
        )
    
    # ===== ОБРАБОТЧИКИ КНОПОК =====
    
    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
    
        user_id = str(update.effective_user.id)
        callback_data = query.data
    
    # Обрабатываем выбор AI
        if callback_data.startswith("ai_"):
            ai_type = callback_data[3:]
            await self._start_game_with_ai(query, user_id, ai_type)
    
    # Обрабатываем игровые действия
        elif callback_data.startswith("game_"):
            action = callback_data[5:]
            await self._handle_game_action(query, user_id, action)
    
    # Обрабатываем анализ ← ДОБАВЬ ЭТОТ БЛОК
        elif callback_data.startswith("analyze_"):
            await self._handle_analysis(query, callback_data[8:])
    
    # Обрабатываем выбор позиции ← ДОБАВЬ ЭТОТ БЛОК
        elif callback_data.startswith("position_"):
            await self._handle_position_selection(query, callback_data[9:]) 

    async def _handle_analysis(self, query, analysis_type: str):
        """Обработчик анализа"""
        from app.game_menus import AnalysisMenus  # ← ДОБАВЬ ЭТОТ ИМПОРТ
    
        if analysis_type == "preflop":
            await query.edit_message_text(
                "🃏 **Анализ префлоп руки**\n\n"
                "Выберите вашу позицию за столом:",
                reply_markup=AnalysisMenus.get_position_selection_menu()
            )
        elif analysis_type == "postflop":
            await query.edit_message_text(
                "📊 **Анализ постфлопа**\n\n"
                "Эта функция в разработке. Используйте анализ префлопа.")
        elif analysis_type == "hand_history":
            await query.edit_message_text(
                "📈 **Анализ раздачи**\n\n"
                "Эта функция в разработке. Используйте анализ префлопа.")

    async def _handle_position_selection(self, query, position: str):
        """Обработчик выбора позиции"""
    # Сохраняем позицию в контексте
        context = query.data.split('_')[-1]
    
        await query.edit_message_text(
            f"🎪 **Позиция: {self._get_position_name(position)}**\n\n"
            f"Отправьте ваши карты в формате:\n"
            f"**AKs** - Ace-King suited\n"
            f"**QJo** - Queen-Jack offsuit\n"
            f"**TT** - пара десяток\n\n"
            f"Примеры: AKs, QJo, 99, T2s")
    
    # Сохраняем состояние ожидания ввода карт
        self.waiting_for_cards = {
            "user_id": query.from_user.id,
            "position": position,
            "message_id": query.message.message_id}

    def _get_position_name(self, position: str) -> str:
        """Получить название позиции"""
        names = {
            "early": "Ранняя позиция",
            "middle": "Средняя позиция", 
            "late": "Поздняя позиция",
            "blinds": "Блайнды"}
        return names.get(position, "Неизвестная позиция")

    async def _handle_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /analyze"""
        from app.game_menus import AnalysisMenus  # ← ДОБАВЬ ЭТОТ ИМПОРТ
    
        await update.message.reply_text(
        "📊 **Анализ покерных рук**\n\n"
        "Выберите тип анализа:",
        reply_markup=AnalysisMenus.get_analysis_menu())

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        text = update.message.text.strip()  # ← ДОБАВЬ .strip()
        user_id = update.effective_user.id


        if hasattr(self, 'waiting_for_cards') and self.waiting_for_cards["user_id"] == user_id:
            await self._process_hand_input(update, text)
            return
        # Обрабатываем кнопки главного меню
        if text == "🎮 Быстрая игра":
            await self._handle_test_game(update, context)
        elif text == "📊 Анализ руки":
            await self._handle_analyze(update, context)  # ← ИЗМЕНИ ЭТУ СТРОКУ
        elif text == "📈 Моя статистика":
            await update.message.reply_text("📈 Статистика - в разработке")
        elif text == "👤 Мой профиль":
            await update.message.reply_text("👤 Профиль - в разработке")
        elif text == "📚 Обучение":
            await update.message.reply_text("📚 Обучение - в разработке")
        elif text == "⚙️ Настроить игру":
            await update.message.reply_text("⚙️ Настройка игры - в разработке")
        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню или команды!")
    
    # ===== ИГРОВАЯ ЛОГИКА =====
    
    async def _start_game_with_ai(self, query, user_id: str, ai_type: str):
        """Начать игру с выбранным AI"""
        try:
            # Создаем игру
            game = self.game_manager.create_game(user_id, ai_type)
            game_state = self.game_manager.get_game_state(user_id)
            
            # Отправляем информацию о игре
            game_text = TextTemplates.get_game_start_text(
                game_state["ai_name"],
                GameMenus.get_ai_description(ai_type),
                game_state["user_cards"],
                game_state["user_stack"],
                game_state["pot"]
            )
            
            await query.edit_message_text(game_text)
            await self._show_game_actions_by_chat(
                query, query.message.chat_id, user_id
            )
            
        except Exception as e:
            await query.edit_message_text(f"Ошибка начала игры: {e}")
    
    async def _handle_game_action(self, query, user_id: str, action: str):
        """Обработать игровое действие"""
        # Обрабатываем действие через менеджер игр
        result = self.game_manager.process_player_action(user_id, action)
        
        if "error" in result:
            await query.edit_message_text(result["error"])
            return
        
        # Формируем ответ
        response_text = result["message"]
        if "ai_message" in result:
            response_text += f"\n{result['ai_message']}"
        
        response_text += f"\n\n💰 Банк: {result['pot']} BB"
        response_text += f"\n💵 Ваш стек: {result['player_stack']} BB"
        
        # Добавляем информацию о community cards
        if result.get("community_cards"):
            street = "Флоп" if len(result["community_cards"]) == 3 else "Терн" if len(result["community_cards"]) == 4 else "Ривер"
            response_text += f"\n\n🃏 {street}: {' '.join(str(card) for card in result['community_cards'])}"
        
        # Обрабатываем завершение игры
        if not result.get("game_continues", True):
            if "winner" in result:
                response_text += f"\n\n🏆 Победитель: {result['winner']}"
                response_text += f"\n🎯 Комбинация: {result['winning_hand']}"
            self.game_manager.end_game(user_id)
            await query.edit_message_text(response_text)
            return
        
        # Продолжаем игру
        await query.edit_message_text(response_text)
        await self._show_game_actions_by_chat(query, query.message.chat_id, user_id)
    
    # ===== УТИЛИТЫ ДЛЯ ОТОБРАЖЕНИЯ =====
    
    async def _show_game_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str):
        """Показать игровые действия"""
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Выберите действие:",
            reply_markup=GameMenus.get_game_actions_menu()
        )
    
    async def _show_game_actions_by_chat(self, update, chat_id: int, user_id: str):
        """Показать игровые действия по chat_id"""
        await update._bot.send_message(
            chat_id=chat_id,
            text="Выберите действие:",
            reply_markup=GameMenus.get_game_actions_menu()
        )
    
    async def _process_hand_input(self, update: Update, hand_input: str):
        """Обработать ввод руки для анализа"""
        try:
            from app.poker_engine import Card, Rank, Suit  # ← ДОБАВЬ ЭТОТ ИМПОРТ
        
        # Получаем сохраненное состояние
            waiting_data = self.waiting_for_cards
            position = waiting_data["position"]
        
        # Парсим ввод руки
            cards = self._parse_hand_input(hand_input)
            if not cards:
                await update.message.reply_text(
                "❌ Неверный формат руки. Используйте формат: AKs, QJo, 99 и т.д.\n"
                "Попробуйте снова:")
                return
        
        # Анализируем руку
            analysis = hand_analyzer.analyze_preflop_hand(cards, position)
        
        # Отправляем результат
            analysis_text = TextTemplates.get_hand_analysis_text(analysis)
            await update.message.reply_text(analysis_text, parse_mode='Markdown')
        
        # Очищаем состояние ожидания
            del self.waiting_for_cards
        
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка анализа: {e}")
            if hasattr(self, 'waiting_for_cards'):
                del self.waiting_for_cards

    def _parse_hand_input(self, hand_input: str):
        """Парсить текстовый ввод руки в карты"""
        from app.poker_engine import Card, Rank, Suit  # ← ДОБАВЬ ЭТОТ ИМПОРТ
    
    # Простой парсер для демонстрации
        if len(hand_input) < 2:
            return None
    
    # Маппинг символов в ранги
        rank_map = {
            'A': Rank.ACE, 'K': Rank.KING, 'Q': Rank.QUEEN, 'J': Rank.JACK,
            'T': Rank.TEN, '9': Rank.NINE, '8': Rank.EIGHT, '7': Rank.SEVEN,
            '6': Rank.SIX, '5': Rank.FIVE, '4': Rank.FOUR, '3': Rank.THREE, '2': Rank.TWO}
    
        try:
        # Парсим формат типа "AKs", "QJo", "99"
            if len(hand_input) == 2:
            # Пара
                rank_char = hand_input[0]
                if rank_char not in rank_map:
                    return None
                rank = rank_map[rank_char]
                return [Card(rank, Suit.HEARTS), Card(rank, Suit.DIAMONDS)]
        
            elif len(hand_input) == 3:
            # Две карты
                rank1_char, rank2_char, suit_indicator = hand_input
            
                if rank1_char not in rank_map or rank2_char not in rank_map:
                    return None
            
                rank1 = rank_map[rank1_char]
                rank2 = rank_map[rank2_char]
            
                if suit_indicator == 's':
                # suited
                    return [Card(rank1, Suit.HEARTS), Card(rank2, Suit.HEARTS)]
                elif suit_indicator == 'o':
                # offsuit
                    return [Card(rank1, Suit.HEARTS), Card(rank2, Suit.DIAMONDS)]
                else:
                    return None
        
            return None
        
        except Exception:
            return None

    def run(self):
        """Запуск бота"""
        logger.info("Starting Poker Mentor Bot...")
        print("🤖 Запуск Poker Mentor Bot...")
        print("🛑 Для остановки нажмите Ctrl+C")
        self.application.run_polling()
# ДОБАВИТЬ в класс PokerMentorBot:

    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки с улучшенной обработкой ошибок"""
        try:
            query = update.callback_query
            await query.answer()
        
            user_id = str(update.effective_user.id)
            callback_data = query.data

        # Обрабатываем выбор AI
            if callback_data.startswith("ai_"):
                ai_type = callback_data[3:]
                await self._start_game_with_ai(query, user_id, ai_type)

        # Обрабатываем игровые действия
            elif callback_data.startswith("game_"):
                action = callback_data[5:]
                await self._handle_game_action(query, user_id, action)

        # Обрабатываем анализ
            elif callback_data.startswith("analyze_"):
                await self._handle_analysis(query, callback_data[8:])

        # Обрабатываем выбор позиции
            elif callback_data.startswith("position_"):
                await self._handle_position_selection(query, callback_data[9:])
            
            else:
                await query.edit_message_text("❌ Неизвестная команда")

        except Exception as e:
            logger.error(f"Ошибка в callback: {e}")
            await update.callback_query.edit_message_text("❌ Произошла ошибка. Попробуйте снова.")

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений с улучшенной обработкой ошибок"""
        try:
            text = update.message.text.strip()
            user_id = update.effective_user.id

            # Проверяем ожидание ввода карт
            if hasattr(self, 'waiting_for_cards') and self.waiting_for_cards.get("user_id") == user_id:
                await self._process_hand_input(update, text)
                return

        # Обрабатываем кнопки главного меню
            menu_actions = {
                "🎮 Быстрая игра": self._handle_test_game,
                "📊 Анализ руки": self._handle_analyze,
                "📈 Моя статистика": lambda u, c: u.message.reply_text("📈 Статистика - в разработке"),
                "👤 Мой профиль": lambda u, c: u.message.reply_text("👤 Профиль - в разработке"),
                "📚 Обучение": lambda u, c: u.message.reply_text("📚 Обучение - в разработке"),
                "⚙️ Настроить игру": lambda u, c: u.message.reply_text("⚙️ Настройка игры - в разработке")
            }

            if text in menu_actions:
                await menu_actions[text](update, context)
            else:
                await update.message.reply_text(
                    "🤔 Я не понял команду. Пожалуйста, используйте кнопки меню!",
                    reply_markup=GameMenus.get_main_menu()
                )
            
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте снова.")

    async def _handle_debug(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для отладки (/debug)"""
        user_id = update.effective_user.id
        debug_info = f"""
🔧  **Отладочная информация**

    👤 Пользователь: {user_id}
    🎮 Активных игр: {len(self.game_manager.active_games)}
    💾 База данных: {config.get('DATABASE_URL')}

    📊 Статистика:
    • Пользователей в БД: {self._get_user_count()}
    • Игровых сессий: {self._get_session_count()}
        """
        await update.message.reply_text(debug_info)

    async def _handle_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать историю игр"""
        user_id = update.effective_user.id
        sessions = history_manager.get_recent_sessions(user_id, 5)
    
        if not sessions:
            await update.message.reply_text("📝 У вас еще нет сыгранных сессий")
            return
    
        text = "📊 **Последние игры:**\n\n"
        for session in sessions:
            text += f"🕐 **{session['date']}**\n"
            text += f"🤖 Оппонент: {session['opponent']}\n"
            text += f"🎯 Рук: {session['hands_played']} | Результат: {session['result']}\n"
            text += f"⏱️ Длительность: {session['duration']}\n\n"
    
        await update.message.reply_text(text, parse_mode='Markdown')

    async def _handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику"""
        user_id = update.effective_user.id
        stats = stats_manager.get_user_stats(user_id)
    
        text = "📈 **Ваша статистика:**\n\n"
        text += f"🎓 **Уровень:** {stats['level'].title()}\n"
        text += f"🃏 **Сыграно рук:** {stats['total_hands']}\n"
        text += f"📊 **Винрейт:** {stats['win_rate']}\n"
        text += f"🎯 **VPIP/PFR:** {stats['vpip']}/{stats['pfr']}\n"
        text += f"⚡ **Агрессия:** {stats['aggression']}\n\n"
    
        text += "⭐ **Лучшая рука:** {stats['best_hand']}\n"
        text += "💡 **Основная утечка:** {stats['worst_leak']}\n"
        text += "📈 **Прогресс за месяц:** {stats['monthly_progress']}\n\n"
    
        text += "_Используйте /history для просмотра последних игр_"
    
        await update.message.reply_text(text, parse_mode='Markdown')
    async def _handle_ml_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус ML системы"""
        status = model_trainer.get_training_status()
    
        text = "🤖 **Статус ML системы:**\n\n"
        text += f"📊 **Данных собрано:** {status['data_collected']}\n"
        text += f"🎯 **Статус:** {status['status']}\n"
        text += f"💡 **Рекомендация:** {status['recommendation']}\n\n"
    
        if status['data_collected'] > 0:
            text += "_Используйте /train_ml для запуска обучения_"
    
        await update.message.reply_text(text, parse_mode='Markdown')

    async def _handle_train_ml(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск обучения ML модели"""
        result = model_trainer.start_training()
    
        text = "🎯 **Результат обучения ML:**\n\n"
    
        if result['status'] == 'success':
            text += "✅ **Обучение завершено!**\n"
            text += f"📈 **Точность:** {result['accuracy']}\n"
            text += f"💡 **Следующий шаг:** {result['next_step']}\n"
        elif result['status'] == 'need_more_data':
            text += "📊 **Нужно больше данных:**\n"
            text += f"📝 {result['message']}\n"
            text += "💡 _Продолжайте играть для сбора данных_"
        else:
            text += "❌ **Ошибка обучения:**\n"
            text += f"⚠️ {result['message']}"
    
        await update.message.reply_text(text, parse_mode='Markdown')

        
# Точка входа
if __name__ == "__main__":
    try:
        bot = PokerMentorBot()
        bot.run()
    except ValueError as e:
        print(f"❌ Ошибка запуска: {e}")
        print("\n🔧 Инструкция по настройке:")
        print("1. Откройте файл config.txt")
        print("2. Замените 'your_bot_token_here' на ваш токен от @BotFather")
        print("3. Сохраните файл и запустите бота снова")
    except Exception as e:
        print(f"💥 Неожиданная ошибка: {e}")