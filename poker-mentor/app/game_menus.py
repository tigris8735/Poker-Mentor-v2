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
