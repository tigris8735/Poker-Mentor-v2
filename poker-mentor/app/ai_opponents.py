import random
import logging
from typing import List, Dict, Tuple
from app.poker_engine import PokerGame, Action, Card, Rank, Suit

logger = logging.getLogger(__name__)

class BaseAI:
    """Базовый класс для AI оппонентов"""
    
    def __init__(self, name: str, aggression: float, tightness: float):
        self.name = name
        self.aggression = aggression  # 0-1: склонность к рейзам
        self.tightness = tightness    # 0-1: склонность играть только сильные руки
        
    def decide_action(self, game: PokerGame, player: str) -> Tuple[Action, int]:
        """Принять решение о действии"""
        raise NotImplementedError

class FishAI(BaseAI):
    """Рыба - играет много рук, пассивная"""
    
    def __init__(self):
        super().__init__("Fish", aggression=0.2, tightness=0.3)
    
    def decide_action(self, game: PokerGame, player: str) -> Tuple[Action, int]:
        cards = game.player_cards[player]
        
        # Рыба играет много рук
        if self._should_fold(cards):
            return Action.FOLD, 0
        
        # Пассивная игра - в основном чек/колл
        if random.random() < 0.8:  # 80% чек/колл
            if game.current_bet > 0:
                return Action.CALL, game.current_bet
            else:
                return Action.CHECK, 0
        else:  # 20% рейз
            raise_amount = max(game.big_blind, int(game.current_bet * 1.5))
            return Action.RAISE, raise_amount
    
    def _should_fold(self, cards: List[Card]) -> bool:
        """Рыба фолдит только очень слабые руки"""
        ranks = [card.rank for card in cards]
        
        # Очень слабые руки: 2-7, 2-8 без suited/connected
        weak_ranks = [Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, Rank.SEVEN]
        if all(rank in weak_ranks for rank in ranks):
            return random.random() < 0.7  # 70% фолд слабых рук
        
        return False

class NitAI(BaseAI):
    """Нит - играет только премиум руки, очень тайтовый"""
    
    def __init__(self):
        super().__init__("Nit", aggression=0.4, tightness=0.9)
    
    def decide_action(self, game: PokerGame, player: str) -> Tuple[Action, int]:
        cards = game.player_cards[player]
        
        # Нит играет только сильные руки
        hand_strength = self._evaluate_hand_strength(cards)
        
        if hand_strength < 0.3:  # Слабые руки - фолд
            return Action.FOLD, 0
        elif hand_strength < 0.6:  # Средние руки - чек/колл
            if game.current_bet > 0:
                return Action.CALL, game.current_bet
            else:
                return Action.CHECK, 0
        else:  # Сильные руки - рейз
            raise_amount = max(game.big_blind * 3, int(game.current_bet * 2))
            return Action.RAISE, raise_amount
    
    def _evaluate_hand_strength(self, cards: List[Card]) -> float:
        """Оценка силы руки для нита"""
        ranks = [card.rank for card in cards]
        suits = [card.suit for card in cards]
        
        # Премиум руки
        premium_pairs = [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK]
        if ranks[0] == ranks[1] and ranks[0] in premium_pairs:
            return 0.9  # AA, KK, QQ, JJ
        
        # suited connectors
        if suits[0] == suits[1]:
            rank_indices = [list(Rank).index(rank) for rank in ranks]
            if abs(rank_indices[0] - rank_indices[1]) <= 2:
                return 0.7  # suited connectors
        
        # High cards
        if any(rank in premium_pairs for rank in ranks):
            return 0.5
        
        return 0.2  # Слабые руки

class TAGAI(BaseAI):
    """TAG (Tight Aggressive) - тайтовый агрессивный"""
    
    def __init__(self):
        super().__init__("TAG", aggression=0.7, tightness=0.7)
    
    def decide_action(self, game: PokerGame, player: str) -> Tuple[Action, int]:
        cards = game.player_cards[player]
        hand_strength = self._evaluate_hand_strength(cards)
        
        if hand_strength < 0.4:  # Фолд слабых рук
            return Action.FOLD, 0
        
        # Агрессивная игра с сильными руками
        if hand_strength > 0.7:
            if game.current_bet == 0:
                raise_amount = game.big_blind * 3
                return Action.RAISE, raise_amount
            else:
                return Action.RAISE, int(game.current_bet * 2.5)
        
        # Умеренная игра со средними руками
        if game.current_bet > 0:
            return Action.CALL, game.current_bet
        else:
            return Action.CHECK, 0
    
    def _evaluate_hand_strength(self, cards: List[Card]) -> float:
        """Оценка силы руки для TAG"""
        # Более сложная логика оценки
        ranks = [card.rank for card in cards]
        suits = [card.suit for card in cards]
        
        # Пары
        if ranks[0] == ranks[1]:
            pair_value = list(Rank).index(ranks[0]) / len(Rank)
            return 0.5 + pair_value * 0.5
        
        # suited
        if suits[0] == suits[1]:
            rank_indices = sorted([list(Rank).index(rank) for rank in ranks])
            connector_bonus = 1.0 - (rank_indices[1] - rank_indices[0]) * 0.1
            high_card_bonus = rank_indices[1] / len(Rank) * 0.3
            return 0.3 + high_card_bonus + connector_bonus * 0.2
        
        # off-suited
        high_card = max(ranks, key=lambda x: list(Rank).index(x))
        high_card_value = list(Rank).index(high_card) / len(Rank)
        return 0.2 + high_card_value * 0.3

class LAGAI(BaseAI):
    """LAG (Loose Aggressive) - лузовый агрессивный"""
    
    def __init__(self):
        super().__init__("LAG", aggression=0.8, tightness=0.3)
    
    def decide_action(self, game: PokerGame, player: str) -> Tuple[Action, int]:
        # LAG играет агрессивно почти всегда
        if random.random() < 0.7:  # 70% рейз
            if game.current_bet == 0:
                raise_amount = game.big_blind * 2
            else:
                raise_amount = int(game.current_bet * 2)
            return Action.RAISE, raise_amount
        elif game.current_bet > 0:
            return Action.CALL, game.current_bet
        else:
            return Action.CHECK, 0

class AIFactory:
    """Фабрика для создания AI оппонентов"""
    
    @staticmethod
    def create_ai(ai_type: str) -> BaseAI:
        ai_types = {
            "fish": FishAI,
            "nit": NitAI,
            "tag": TAGAI,
            "lag": LAGAI
        }
        
        if ai_type not in ai_types:
            raise ValueError(f"Unknown AI type: {ai_type}")
        
        return ai_types[ai_type]()
    
    @staticmethod
    def get_ai_types() -> List[str]:
        return ["fish", "nit", "tag", "lag"]
    
    # В ai_opponents.py - ОБНОВИТЬ:

@staticmethod
def get_ai_description(ai_type: str) -> str:
    descriptions = {
        "fish": """
🐟 **Fish AI** - Идеально для начинающих
• Играет много рук (лузовый)
• Часто коллирует (пассивный)
• Редко рейзит
• 🤓 Отлично для практики агрессивной игры
        """,
        "nit": """
🛡️ **Nit AI** - Сверхтайтовый оппонент  
• Играет только премиум руки
• Часто фолдит
• Предсказуемая стратегия
• 🎯 Тренируйтесь против тайтовых игроков
        """,
        "tag": """
🎯 **TAG AI** - Балансированная стратегия
• Тайтовый префлоп
• Агрессивный постфлоп
• Сбалансированные диапазоны
• ⚡ Имитирует сильных регалов
        """,
        "lag": """
⚡ **LAG AI** - Агрессивный оппонент
• Лузовый префлоп  
• Частые рейзы и 3-беты
• Давит слабости
• 🔥 Тренируйтесь против агрессии
        """
    }
    return descriptions.get(ai_type, "Неизвестный тип AI")

# Тестирование AI
def test_ai_opponents():
    """Тестирование AI оппонентов"""
    print("🤖 Тестирование AI оппонентов...")
    
    # Создаем тестовую игру
    game = PokerGame(["Player", "AI"])
    game.start_hand()
    
    # Тестируем каждого AI
    for ai_type in AIFactory.get_ai_types():
        ai = AIFactory.create_ai(ai_type)
        action, amount = ai.decide_action(game, "AI")
        print(f"{ai.name}: {action.value} {amount}")

class MLEnhancedAI(BaseAI):
    def __init__(self, base_ai: BaseAI, ml_model):
        self.base_ai = base_ai
        self.ml_model = ml_model
        self.name = f"ML-{base_ai.name}"
        self.confidence_threshold = 0.7
    
    def decide_action(self, game: PokerGame, player: str) -> Tuple[Action, int]:
        # Извлекаем фичи для ML
        features = self._extract_ml_features(game, player)
        
        # Получаем предсказание от ML
        ml_prediction = self.ml_model.predict(features)
        ml_confidence = self.ml_model.get_confidence(features)
        
        if ml_confidence > self.confidence_threshold:
            return self._ml_action_to_game_action(ml_prediction, game)
        else:
            # Fallback на rule-based AI
            return self.base_ai.decide_action(game, player)
        

if __name__ == "__main__":
    test_ai_opponents()