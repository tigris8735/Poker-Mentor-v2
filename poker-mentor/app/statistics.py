import logging
from app.database import db

logger = logging.getLogger(__name__)

class StatisticsManager:
    def __init__(self):
        self.db = db
    
    def get_user_stats(self, telegram_id: int):
        """Основная статистика пользователя"""
        try:
            user_info = self.db.get_user_info(telegram_id)
            return {
                'level': user_info.get('level', 'beginner') if user_info else 'beginner',
                'total_hands': user_info.get('total_hands', 0) if user_info else 0,
                'win_rate': '62%',
                'vpip': '28%',  # Voluntary Put Money In Pot
                'pfr': '18%',   # Preflop Raise
                'aggression': '45%',
                'best_hand': 'A♠ A♥',
                'worst_leak': 'Слишком много блефов',
                'monthly_progress': '+125 BB'
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self):
        return {
            'level': 'beginner',
            'total_hands': 0,
            'win_rate': '0%',
            'vpip': '0%',
            'pfr': '0%',
            'aggression': '0%',
            'best_hand': 'N/A',
            'worst_leak': 'Недостаточно данных',
            'monthly_progress': '0 BB'
        }

stats_manager = StatisticsManager()