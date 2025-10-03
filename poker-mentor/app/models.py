from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, JSON, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class UserLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class GameType(enum.Enum):
    CASH = "cash"
    TOURNAMENT = "tournament"

class SessionStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    level = Column(Enum(UserLevel), default=UserLevel.BEGINNER)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Предпочтения пользователя
    preferred_game_type = Column(Enum(GameType), default=GameType.CASH)
    preferred_stake = Column(String(50), default="1/2")
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

class GameSession(Base):
    __tablename__ = 'game_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    game_type = Column(Enum(GameType), default=GameType.CASH)
    stake_level = Column(String(50), default="1/2")
    ai_opponent_type = Column(String(50), default="balanced")  # fish, tag, lag, nit
    stack_size = Column(Integer, default=100)  # в big blinds
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Статистика сессии
    hands_played = Column(Integer, default=0)
    net_profit = Column(Integer, default=0)  # в big blinds
    
    def __repr__(self):
        return f"<GameSession(id={self.id}, user_id={self.user_id}, status={self.status})>"

class HandHistory(Base):
    __tablename__ = 'hand_histories'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, nullable=False)
    hand_number = Column(Integer, nullable=False)
    
    # Детали раздачи
    positions = Column(JSON)  # {player: position}
    hole_cards = Column(JSON)  # {player: [card1, card2]}
    community_cards = Column(JSON)  # [card1, card2, ...]
    actions = Column(JSON)  # [{street: preflop/flop/turn/river, player: name, action: type, amount: x}]
    result = Column(JSON)  # {winner: player, pot: amount, showdown: boolean}
    
    # Анализ раздачи
    analysis = Column(JSON)  # {equity: %, ev: value, mistakes: [], rating: 1-10}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<HandHistory(id={self.id}, session_id={self.session_id}, hand_number={self.hand_number})>"

class UserStats(Base):
    __tablename__ = 'user_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    
    # Общая статистика
    total_hands_played = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    total_profit = Column(Integer, default=0)  # в big blinds
    
    # Winrate по типам игр
    cash_winrate = Column(Float, default=0.0)
    tournament_winrate = Column(Float, default=0.0)
    
    # Статистика по оппонентам
    vs_fish_winrate = Column(Float, default=0.0)
    vs_tag_winrate = Column(Float, default=0.0)
    vs_lag_winrate = Column(Float, default=0.0)
    vs_nit_winrate = Column(Float, default=0.0)
    
    # Анализ ошибок
    common_mistakes = Column(JSON, default=[])
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserStats(user_id={self.user_id}, hands_played={self.total_hands_played})>"