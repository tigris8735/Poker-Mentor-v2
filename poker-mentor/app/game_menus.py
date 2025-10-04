from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from app.ai_opponents import AIFactory
# В game_menus.py - ДОБАВИТЬ в начало
from typing import Dict, List, Any, Optional, Tuple

class GameMenus:
    """Класс для управления всеми меню и кнопками"""
    
    @staticmethod
    def get_main_menu():
        """Главное меню бота"""
        keyboard = [
            ["🎮 Быстрая игра", "⚙️ Настроить игру"],
            ["📊 Анализ руки", "📈 Моя статистика"],
            ["📚 Обучение", "👤 Мой профиль"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def get_ai_selection_menu():
        """Меню выбора AI оппонента"""
        keyboard = [
            [InlineKeyboardButton("🐟 Fish AI", callback_data="ai_fish")],
            [InlineKeyboardButton("🛡️ Nit AI", callback_data="ai_nit")],
            [InlineKeyboardButton("🎯 TAG AI", callback_data="ai_tag")],
            [InlineKeyboardButton("⚡ LAG AI", callback_data="ai_lag")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_game_actions_menu():
        """Меню игровых действий"""
        keyboard = [
            [InlineKeyboardButton("📥 Колл", callback_data="game_call")],
            [InlineKeyboardButton("📤 Рейз", callback_data="game_raise")],
            [InlineKeyboardButton("❌ Фолд", callback_data="game_fold")],
            [InlineKeyboardButton("⚖️ Чек", callback_data="game_check")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_ai_description(ai_type: str) -> str:
        """Получить описание AI оппонента"""
        return AIFactory.get_ai_description(ai_type)

# В game_menus.py - ОБНОВИТЬ TextTemplates:

class TextTemplates:
    """Улучшенные текстовые шаблоны"""
    
    @staticmethod
    def get_welcome_text(user_name: str, level: str, hands_played: int) -> str:
        level_emojis = {
            "beginner": "🟢",
            "intermediate": "🟡", 
            "advanced": "🔴"
        }
        
        return f"""
🎉 Добро пожаловать в Poker Mentor, {user_name}!

{level_emojis.get(level, '🎓')} **Ваш уровень:** {level.title()}
📊 **Сыграно раздач:** {hands_played}

🚀 **Доступные функции:**
• 🎮 Игра против AI с разными стилями
• 📊 Анализ ваших раздач  
• 📚 Обучение стратегиям
• 📈 Отслеживание прогресса

💡 **Совет:** Начните с быстрой игры против Fish AI чтобы попрактиковаться!

Выберите действие из меню ниже 👇
        """
    
    @staticmethod
    def get_hand_analysis_text(analysis: Dict) -> str:
        """Улучшенный текст анализа руки"""
        if "error" in analysis:
            return f"❌ {analysis['error']}"
            
        strength_bar = "█" * int(analysis['strength'] * 10) + "▒" * (10 - int(analysis['strength'] * 10))
        
        return f"""
📊 **Анализ руки: {analysis['hand'].upper()}**

💪 **Сила:** {analysis['strength']:.2f} 
{strength_bar}
🏷️ **Категория:** {analysis['category']}
🎪 **Позиция:** {analysis['position']}
🎯 **Тип:** {'Пара' if analysis['is_pair'] else 'Suited' if analysis['suited'] else 'Offsuit'}

📋 **Рекомендации:**
{chr(10).join('• ' + rec for rec in analysis['recommendations'])}

💡 *Используйте эти рекомендации для принятия решения*
        """

# Добавляем новые меню
class AnalysisMenus:
    """Меню для анализа"""
    
    @staticmethod
    def get_analysis_menu():
        """Меню анализа"""
        keyboard = [
            [InlineKeyboardButton("🃏 Анализ префлоп руки", callback_data="analyze_preflop")],
            [InlineKeyboardButton("📊 Анализ постфлопа", callback_data="analyze_postflop")],
            [InlineKeyboardButton("📈 Анализ раздачи", callback_data="analyze_hand_history")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_position_selection_menu():
        """Меню выбора позиции"""
        keyboard = [
            [InlineKeyboardButton("🎪 Ранняя позиция", callback_data="position_early")],
            [InlineKeyboardButton("🎪 Средняя позиция", callback_data="position_middle")],
            [InlineKeyboardButton("🎪 Поздняя позиция", callback_data="position_late")],
            [InlineKeyboardButton("🎪 Блайнды", callback_data="position_blinds")],
        ]
        return InlineKeyboardMarkup(keyboard)

## настройки игры +++ 

class SettingsMenus:
    """Меню для настройки игры"""
    
    @staticmethod
    def get_settings_menu():
        """Меню настроек игры"""
        keyboard = [
            [InlineKeyboardButton("🤖 Тип оппонента", callback_data="settings_ai")],
            [InlineKeyboardButton("💰 Размер ставок", callback_data="settings_stakes")],
            [InlineKeyboardButton("🎯 Уровень сложности", callback_data="settings_difficulty")],
            [InlineKeyboardButton("📊 Тип игры", callback_data="settings_gametype")],
            [InlineKeyboardButton("💾 Сохранить настройки", callback_data="settings_save")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_ai_settings_menu():
        """Меню выбора типа AI"""
        keyboard = [
            [InlineKeyboardButton("🐟 Fish", callback_data="set_ai_fish")],
            [InlineKeyboardButton("🛡️ Nit", callback_data="set_ai_nit")],
            [InlineKeyboardButton("🎯 TAG", callback_data="set_ai_tag")],
            [InlineKeyboardButton("⚡ LAG", callback_data="set_ai_lag")],
            [InlineKeyboardButton("🔙 Назад", callback_data="settings_back")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_stakes_menu():
        """Меню выбора ставок"""
        keyboard = [
            [InlineKeyboardButton("💰 1/2", callback_data="set_stakes_1_2")],
            [InlineKeyboardButton("💰 2/4", callback_data="set_stakes_2_4")],
            [InlineKeyboardButton("💰 5/10", callback_data="set_stakes_5_10")],
            [InlineKeyboardButton("🔙 Назад", callback_data="settings_back")]
        ]
        return InlineKeyboardMarkup(keyboard)

class ProfileMenus:
    """Меню профиля пользователя"""
    
    @staticmethod
    def get_profile_menu():
        """Меню профиля"""
        keyboard = [
            [InlineKeyboardButton("🎓 Изменить уровень", callback_data="profile_level")],
            [InlineKeyboardButton("📅 История активности", callback_data="profile_activity")],
            [InlineKeyboardButton("🏆 Достижения", callback_data="profile_achievements")],
            [InlineKeyboardButton("🔙 Назад", callback_data="profile_back")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_level_selection_menu():
        """Выбор уровня навыков"""
        keyboard = [
            [InlineKeyboardButton("🟢 Новичок", callback_data="set_level_beginner")],
            [InlineKeyboardButton("🟡 Любитель", callback_data="set_level_intermediate")],
            [InlineKeyboardButton("🔴 Продвинутый", callback_data="set_level_advanced")],
            [InlineKeyboardButton("🔙 Назад", callback_data="profile_back")]
        ]
        return InlineKeyboardMarkup(keyboard)
    

class LearningMenus:
    """Меню обучения"""
    
    @staticmethod
    def get_learning_menu():
        """Главное меню обучения"""
        keyboard = [
            [InlineKeyboardButton("🎯 Основы покера", callback_data="learn_basics")],
            [InlineKeyboardButton("📊 Префлоп стратегия", callback_data="learn_preflop")],
            [InlineKeyboardButton("🃏 Постфлоп игра", callback_data="learn_postflop")],
            [InlineKeyboardButton("🧮 Математика покера", callback_data="learn_math")],
            [InlineKeyboardButton("🤖 Против AI", callback_data="learn_vs_ai")],
            [InlineKeyboardButton("🔙 Назад", callback_data="learning_back")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_lesson_menu(lesson_type: str):
        """Меню конкретного урока"""
        lessons = {
            "basics": [
                ["📖 Правила игры", "lesson_basics_rules"],
                ["🎯 Комбинации", "lesson_basics_combinations"],
                ["💰 Блайнды и ставки", "lesson_basics_blinds"],
                ["🔙 Назад", "learning_back"]
            ],
            "preflop": [
                ["🃏 Стартовые руки", "lesson_preflop_hands"],
                ["🎪 Позиционная игра", "lesson_preflop_position"],
                ["📈 Рейнжи оппонентов", "lesson_preflop_ranges"],
                ["🔙 Назад", "learning_back"]
            ]
        }
        
        if lesson_type in lessons:
            return InlineKeyboardMarkup(lessons[lesson_type])
        return LearningMenus.get_learning_menu()