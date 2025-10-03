import random
import logging
from enum import Enum
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

class Action(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

class HandType(Enum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit
    
    def __repr__(self):
        return f"{self.rank.value}{self.suit.value}"
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

class Deck:
    def __init__(self):
        self.cards = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()
    
    def shuffle(self):
        """Перетасовать колоду"""
        random.shuffle(self.cards)
        logger.debug("Колода перетасована")
    
    def deal(self, num_cards: int = 1) -> List[Card]:
        """Раздать карты"""
        if num_cards > len(self.cards):
            raise ValueError("Недостаточно карт в колоде")
        
        dealt_cards = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        return dealt_cards

class PokerHand:
    def __init__(self, cards: List[Card]):
        if len(cards) != 5:
            raise ValueError("Покерная рука должна содержать 5 карт")
        self.cards = sorted(cards, key=lambda x: list(Rank).index(x.rank), reverse=True)
        self.hand_type, self.hand_value = self._evaluate_hand()
    
    def _evaluate_hand(self) -> Tuple[HandType, List[int]]:
        """Оценка силы руки"""
        ranks = [card.rank for card in self.cards]
        suits = [card.suit for card in self.cards]
        
        rank_counts = {rank: ranks.count(rank) for rank in set(ranks)}
        suit_counts = {suit: suits.count(suit) for suit in set(suits)}
        
        sorted_ranks = sorted(set(ranks), key=lambda x: list(Rank).index(x), reverse=True)
        
        # Проверка на флеш
        is_flush = len(set(suits)) == 1
        
        # Проверка на стрит
        rank_indices = sorted([list(Rank).index(rank) for rank in ranks])
        is_straight = len(set(rank_indices)) == 5 and (rank_indices[-1] - rank_indices[0] == 4 or 
                     (rank_indices == [0, 1, 2, 3, 12] and ranks.count(Rank.ACE) == 1))  # Стрит с тузом как 1
        
        # Роял флеш
        if is_flush and is_straight and Rank.ACE in ranks and Rank.KING in ranks:
            return HandType.ROYAL_FLUSH, [10]
        
        # Стрит флеш
        if is_flush and is_straight:
            return HandType.STRAIGHT_FLUSH, [list(Rank).index(max(ranks, key=lambda x: list(Rank).index(x)))]
        
        # Каре
        if 4 in rank_counts.values():
            quad_rank = [rank for rank, count in rank_counts.items() if count == 4][0]
            kicker = [rank for rank in ranks if rank != quad_rank][0]
            return HandType.FOUR_OF_A_KIND, [list(Rank).index(quad_rank), list(Rank).index(kicker)]
        
        # Фулл хаус
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            triple_rank = [rank for rank, count in rank_counts.items() if count == 3][0]
            pair_rank = [rank for rank, count in rank_counts.items() if count == 2][0]
            return HandType.FULL_HOUSE, [list(Rank).index(triple_rank), list(Rank).index(pair_rank)]
        
        # Флеш
        if is_flush:
            return HandType.FLUSH, [list(Rank).index(rank) for rank in sorted_ranks]
        
        # Стрит
        if is_straight:
            return HandType.STRAIGHT, [list(Rank).index(max(ranks, key=lambda x: list(Rank).index(x)))]
        
        # Тройка
        if 3 in rank_counts.values():
            triple_rank = [rank for rank, count in rank_counts.items() if count == 3][0]
            kickers = [rank for rank in ranks if rank != triple_rank]
            kicker_values = [list(Rank).index(rank) for rank in sorted(kickers, key=lambda x: list(Rank).index(x), reverse=True)]
            return HandType.THREE_OF_A_KIND, [list(Rank).index(triple_rank)] + kicker_values
        
        # Две пары
        pairs = [rank for rank, count in rank_counts.items() if count == 2]
        if len(pairs) == 2:
            pair_ranks = sorted(pairs, key=lambda x: list(Rank).index(x), reverse=True)
            kicker = [rank for rank in ranks if rank not in pair_ranks][0]
            return HandType.TWO_PAIR, [list(Rank).index(pair_ranks[0]), list(Rank).index(pair_ranks[1]), list(Rank).index(kicker)]
        
        # Одна пара
        if 2 in rank_counts.values():
            pair_rank = [rank for rank, count in rank_counts.items() if count == 2][0]
            kickers = [rank for rank in ranks if rank != pair_rank]
            kicker_values = [list(Rank).index(rank) for rank in sorted(kickers, key=lambda x: list(Rank).index(x), reverse=True)]
            return HandType.ONE_PAIR, [list(Rank).index(pair_rank)] + kicker_values
        
        # Старшая карта
        return HandType.HIGH_CARD, [list(Rank).index(rank) for rank in sorted_ranks]
    
    def __lt__(self, other):
        if self.hand_type.value != other.hand_type.value:
            return self.hand_type.value < other.hand_type.value
        return self.hand_value < other.hand_value
    
    def __eq__(self, other):
        return self.hand_type == other.hand_type and self.hand_value == other.hand_value

class PokerGame:
    def __init__(self, players: List[str], small_blind: int = 1, big_blind: int = 2):
        self.players = players
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.player_stacks = {player: 100 for player in players}  # Стартовый стек 100 BB
        self.player_cards = {player: [] for player in players}
        self.current_player_idx = 0
        self.hand_history = []
        
        logger.info(f"Создана новая игра: {players}")
    
    def start_hand(self):
        """Начать новую раздачу"""
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.player_cards = {player: [] for player in self.players}
        self.hand_history = []
        
        # Раздача карт
        for player in self.players:
            self.player_cards[player] = self.deck.deal(2)
        
        logger.info("Начата новая раздача")
        return self.player_cards
    
    def post_blinds(self):
        """Выставить блайнды"""
        sb_player = self.players[0]
        bb_player = self.players[1]
        
        self.player_stacks[sb_player] -= self.small_blind
        self.player_stacks[bb_player] -= self.big_blind
        self.pot = self.small_blind + self.big_blind
        self.current_bet = self.big_blind
        
        logger.info(f"Блайнды: {sb_player} ({self.small_blind}), {bb_player} ({self.big_blind})")
    
    def deal_flop(self):
        """Раздать флоп"""
        self.deck.deal(1)  # Сжечь карту
        self.community_cards.extend(self.deck.deal(3))
        logger.info(f"Флоп: {self.community_cards}")
    
    def deal_turn(self):
        """Раздать терн"""
        self.deck.deal(1)  # Сжечь карту
        self.community_cards.extend(self.deck.deal(1))
        logger.info(f"Терн: {self.community_cards[-1]}")
    
    def deal_river(self):
        """Раздать ривер"""
        self.deck.deal(1)  # Сжечь карту
        self.community_cards.extend(self.deck.deal(1))
        logger.info(f"Ривер: {self.community_cards[-1]}")
    
    def evaluate_showdown(self) -> Dict[str, Tuple[HandType, List[int]]]:
        """Определить победителя на шоудауне"""
        best_hands = {}
        
        for player in self.players:
            all_cards = self.player_cards[player] + self.community_cards
            best_hand = None
            
            # Находим лучшую комбинацию из 5 карт
            for i in range(len(all_cards)):
                for j in range(i + 1, len(all_cards)):
                    for k in range(j + 1, len(all_cards)):
                        for l in range(k + 1, len(all_cards)):
                            for m in range(l + 1, len(all_cards)):
                                hand_cards = [all_cards[i], all_cards[j], all_cards[k], all_cards[l], all_cards[m]]
                                current_hand = PokerHand(hand_cards)
                                
                                if best_hand is None or current_hand > best_hand:
                                    best_hand = current_hand
            
            best_hands[player] = (best_hand.hand_type, best_hand.hand_value)
        
        return best_hands
    
    def get_winner(self) -> List[str]:
        """Определить победителя(ей)"""
        if len(self.players) == 1:
            return self.players
        
        best_hands = self.evaluate_showdown()
        best_hand_value = None
        winners = []
        
        for player, (hand_type, hand_value) in best_hands.items():
            if best_hand_value is None or (hand_type.value, hand_value) > best_hand_value:
                best_hand_value = (hand_type.value, hand_value)
                winners = [player]
            elif (hand_type.value, hand_value) == best_hand_value:
                winners.append(player)
        
        logger.info(f"Победитель(и): {winners} с комбинацией: {best_hands[winners[0]][0]}")
        return winners

# Утилиты для тестирования
def test_poker_engine():
    """Тестирование движка покера"""
    print("🧪 Тестирование покерного движка...")
    
    # Тест колоды
    deck = Deck()
    cards = deck.deal(5)
    print(f"Раздано карт: {cards}")
    
    # Тест оценки руки
    test_hand = PokerHand(cards)
    print(f"Сила руки: {test_hand.hand_type}, Значение: {test_hand.hand_value}")
    
    # Тест игры
    game = PokerGame(["Player1", "Player2"])
    game.start_hand()
    print(f"Карты игроков: {game.player_cards}")
    
    game.post_blinds()
    game.deal_flop()
    game.deal_turn()
    game.deal_river()
    
    winners = game.get_winner()
    print(f"Победители: {winners}")

if __name__ == "__main__":
    test_poker_engine()