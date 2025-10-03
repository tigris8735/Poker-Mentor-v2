import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, GameSession, HandHistory, UserStats
from app.config import config
from datetime import datetime
from app.models import UserLevel, GameType, SessionStatus

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.database_url = config.get('DATABASE_URL', 'sqlite:///poker_mentor.db')
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def init_db(self):
        """Инициализация базы данных - создание таблиц"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("База данных инициализирована")
            print("✅ База данных создана успешно")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise
    
    def get_session(self):
        """Получить сессию БД"""
        return self.SessionLocal()
    
    def add_user(self, telegram_id, username=None, first_name=None, last_name=None):
        """Добавить нового пользователя"""
        session = self.get_session()
        try:
            # Проверяем, существует ли пользователь
            existing_user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if existing_user:
                # Обновляем время активности
                existing_user.last_active = datetime.utcnow()
                session.commit()
                # Возвращаем копию данных, а не сам объект
                return {
                    'id': existing_user.id,
                    'telegram_id': existing_user.telegram_id,
                    'username': existing_user.username,
                    'first_name': existing_user.first_name,
                    'last_name': existing_user.last_name,
                    'level': existing_user.level.value,
                    'created_at': existing_user.created_at
                }
            
            # Создаем нового пользователя
            new_user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            # Создаем статистику для пользователя
            user_stats = UserStats(user_id=new_user.id)
            session.add(user_stats)
            session.commit()
            
            logger.info(f"Создан новый пользователь: {new_user}")
            
            # Возвращаем копию данных, а не сам объект
            return {
                'id': new_user.id,
                'telegram_id': new_user.telegram_id,
                'username': new_user.username,
                'first_name': new_user.first_name,
                'last_name': new_user.last_name,
                'level': new_user.level.value,
                'created_at': new_user.created_at
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка создания пользователя: {e}")
            raise
        finally:
            session.close()
    
    def get_user_info(self, telegram_id):
        """Получить информацию о пользователе без detached объектов"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                return {
                    'id': user.id,
                    'telegram_id': user.telegram_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'level': user.level.value,
                    'created_at': user.created_at
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None
        finally:
            session.close()
    
    def get_user_stats(self, user_id):
        """Получить статистику пользователя"""
        session = self.get_session()
        try:
            stats = session.query(UserStats).filter(UserStats.user_id == user_id).first()
            if stats:
                return {
                    'total_hands_played': stats.total_hands_played,
                    'total_sessions': stats.total_sessions,
                    'total_profit': stats.total_profit
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return None
        finally:
            session.close()
    
    def update_user_activity(self, telegram_id):
        """Обновить время последней активности"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.last_active = datetime.utcnow()
                session.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления активности: {e}")
            session.rollback()
        finally:
            session.close()

# Глобальный объект базы данных
db = Database()