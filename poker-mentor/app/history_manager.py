import logging
from datetime import datetime, timedelta
from app.database import db
import json

logger = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self):
        self.db = db
    
    def get_recent_sessions(self, telegram_id: int, limit: int = 10):
        """Получить последние сессии пользователя"""
        try:
            # Здесь будет реальная логика из БД
            # Пока заглушка с демо-данными
            return [
                {
                    'id': i,
                    'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M'),
                    'opponent': ['Fish AI', 'Nit AI', 'TAG AI', 'LAG AI'][i % 4],
                    'hands_played': 10 + i * 5,
                    'result': f"{['+', '-'][i % 2]}{i * 5 + 15} BB",
                    'duration': f"{15 + i * 5} мин"
                }
                for i in range(1, limit + 1)
            ]
        except Exception as e:
            logger.error(f"Error getting sessions: {e}")
            return []
    
    def get_session_hands(self, session_id: int):
        """Получить раздачи сессии"""
        return [
            {
                'hand_id': f"{session_id}_{i}",
                'cards': ['A♠ K♥', 'Q♦ Q♣', 'J♠ T♠'][i % 3],
                'result': ['Win +15BB', 'Loss -2BB', 'Win +8BB'][i % 3],
                'analysis_rating': [8, 4, 7][i % 3]
            }
            for i in range(5)
        ]

history_manager = HistoryManager()