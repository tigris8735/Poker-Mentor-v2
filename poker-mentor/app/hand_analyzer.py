import logging
from typing import Dict, List, Tuple, Optional
from app.poker_engine import PokerGame, Card, Rank, Suit, HandType

logger = logging.getLogger(__name__)

class HandAnalyzer:
    """Анализатор покерных рук и рекомендаций"""
    
    def __init__(self):
        self.hand_strengths = self._initialize_hand_strengths()
    
    def _initialize_hand_strengths(self) -> Dict[Tuple[str, str], float]:
        """Инициализация силы стартовых рук"""
        strengths = {}
        ranks = [r.value for r in Rank]
        
        # Премиум руки
        premium_pairs = ['A', 'K', 'Q', 'J']
        for i, r1 in enumerate(ranks):
            for j, r2 in enumerate(ranks):
                hand = (r1, r2) if i >= j else (r2, r1)
                strength = self._calculate_hand_strength(hand)
                strengths[hand] = strength
        
        return strengths
    
    def _calculate_hand_strength(self, hand: Tuple[str, str]) -> float:
        """Рассчитать силу стартовой руки"""
        r1, r2 = hand
        
        # Пары
        if r1 == r2:
            pair_strength = {
                'A': 0.99, 'K': 0.98, 'Q': 0.95, 'J': 0.92,
                'T': 0.88, '9': 0.82, '8': 0.78, '7': 0.74,
                '6': 0.70, '5': 0.66, '4': 0.62, '3': 0.58, '2': 0.54
            }
            return pair_strength.get(r1, 0.5)
        
        # suited руки
        suited_bonus = 0.1
        
        # Коннекторы
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                      '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        
        gap = abs(rank_values[r1] - rank_values[r2])
        connector_bonus = max(0, 0.15 - gap * 0.03)
        
        # Базовая сила по старшей карте
        high_card_strength = (rank_values[r1] - 2) / 12 * 0.6
        
        return high_card_strength + suited_bonus + connector_bonus
    
# В hand_analyzer.py - ДОБАВИТЬ:

    def analyze_preflop_hand(self, cards: List[Card], position: str) -> Dict:
        """Анализ префлоп руки с обработкой ошибок"""
        try:
            if len(cards) != 2:
                return {"error": "Для анализа нужно 2 карты"}
        
            card1, card2 = cards
            hand_key = (card1.rank.value, card2.rank.value)
            suited = card1.suit == card2.suit
            is_pair = card1.rank == card2.rank
        
            strength = self.hand_strengths.get(hand_key, 0.5)
        
            # Рекомендации по позиции
            position_multiplier = {
                "early": 0.8,   # Ранняя позиция - играем тайтовее
                "middle": 1.0,  # Средняя позиция
                "late": 1.2,    # Поздняя позиция - играем лузовее
                "blinds": 0.9   # Блайнды
            }.get(position, 1.0)
        
            adjusted_strength = strength * position_multiplier
        
            # Генерация рекомендаций
            recommendations = self._generate_preflop_recommendations(
                cards, adjusted_strength, position
            )
        
            return {
                "hand": f"{card1.rank.value}{card2.rank.value}{'s' if suited else 'o'}",
                "strength": round(adjusted_strength, 2),
                "category": self._get_hand_category(adjusted_strength),
                "recommendations": recommendations,
                "position": position,
                "suited": suited,
                "is_pair": is_pair
            }
        
        except Exception as e:
            logger.error(f"Ошибка анализа руки: {e}")
            return {"error": f"Ошибка анализа: {str(e)}"}
    
    def _get_hand_category(self, strength: float) -> str:
        """Определить категорию руки"""
        if strength >= 0.85:
            return "💎 Премиум"
        elif strength >= 0.75:
            return "🎯 Сильная"
        elif strength >= 0.60:
            return "📊 Средняя"
        elif strength >= 0.45:
            return "🛡️ Маргинальная"
        else:
            return "🗑️ Слабая"
    
    def _generate_preflop_recommendations(self, cards: List[Card], strength: float, position: str) -> List[str]:
        """Сгенерировать рекомендации для префлопа"""
        recommendations = []
        card1, card2 = cards
        
        # Базовые рекомендации по силе руки
        if strength >= 0.8:
            recommendations.append("✅ **Рейз** - сильная рука, нужно агрессивно играть")
            recommendations.append("📈 Можно 3-бетить против рейзов")
        elif strength >= 0.6:
            recommendations.append("✅ **Колл/Рейз** - хорошая рука для игры")
            if position in ["late", "blinds"]:
                recommendations.append("🎯 В поздней позиции можно рейзить")
        elif strength >= 0.45:
            recommendations.append("⚠️ **Осторожно** - играть только в хорошей позиции")
            recommendations.append("📉 Рассмотреть фолд против агрессии")
        else:
            recommendations.append("❌ **Фолд** - слабая рука")
            recommendations.append("💡 Сохраняйте стек для лучших рук")
        
        # Специфические рекомендации
        if card1.rank == card2.rank:
            recommendations.append(f"🔄 **Пара {card1.rank.value}** - играйте агрессивно")
        
        if card1.suit == card2.suit:
            recommendations.append("🌈 **Suited** - дополнительный потенциал для флешей")
        
        # Позиционные рекомендации
        if position == "early":
            recommendations.append("🎪 **Ранняя позиция** - играйте тайтовее")
        elif position == "late":
            recommendations.append("🎪 **Поздняя позиция** - можно играть лузовее")
        
        return recommendations
    
    def analyze_postflop_equity(self, hole_cards: List[Card], community_cards: List[Card], 
                              opponent_range: List[str] = None) -> Dict:
        """Анализ эквити на постфлопе"""
        if len(hole_cards) != 2:
            return {"error": "Нужно 2 карты игрока"}
        
        # Простой расчет эквити (в реальности нужен более сложный алгоритм)
        hand_strength = self._estimate_hand_strength(hole_cards, community_cards)
        equity = self._calculate_rough_equity(hand_strength, len(community_cards))
        
        return {
            "equity": equity,
            "hand_strength": hand_strength,
            "recommendations": self._generate_postflop_recommendations(equity, len(community_cards))
        }
    
    def _estimate_hand_strength(self, hole_cards: List[Card], community_cards: List[Card]) -> float:
        """Оценка силы руки на постфлопе"""
        # Упрощенная оценка (в реальности нужен equity calculator)
        all_cards = hole_cards + community_cards
        
        # Проверка на готовые руки
        if len(community_cards) >= 3:
            # Здесь должна быть логика оценки лучшей комбинации из 5 карт
            return 0.5  # Заглушка
        
        return 0.3  # Базовая оценка
    
    def _calculate_rough_equity(self, hand_strength: float, street: int) -> float:
        """Примерный расчет эквити"""
        # Упрощенная формула (в реальности нужны точные расчеты)
        base_equity = hand_strength
        street_multiplier = {0: 1.0, 3: 0.8, 4: 0.9, 5: 1.0}  # префлоп, флоп, терн, ривер
        
        return min(0.95, base_equity * street_multiplier.get(street, 1.0))
    
    def _generate_postflop_recommendations(self, equity: float, street: int) -> List[str]:
        """Рекомендации для постфлопа"""
        recommendations = []
        
        if equity >= 0.70:
            recommendations.append("🚀 **Агрессивная игра** - у вас сильное эквити")
            recommendations.append("📈 Рейзьте для защиты руки")
        elif equity >= 0.50:
            recommendations.append("✅ **Умеренная игра** - хорошие шансы")
            recommendations.append("⚖️ Колл для сохранения позиции")
        elif equity >= 0.30:
            recommendations.append("⚠️ **Осторожная игра** - слабое эквити")
            recommendations.append("📉 Рассмотрите фолд против агрессии")
        else:
            recommendations.append("❌ **Слабые шансы** - рекомендуется фолд")
            recommendations.append("💡 Сохраняйте стек")
        
        # Рекомендации по улицам
        if street == 3:  # флоп
            recommendations.append("🃏 **Флоп** - оцените потенциал дро")
        elif street == 4:  # терн
            recommendations.append("🃏 **Терн** - многие дро не доехали")
        elif street == 5:  # ривер
            recommendations.append("🃏 **Ривер** - играйте по показанной силе")
        
        return recommendations

class HandHistoryAnalyzer:
    """Анализатор истории рук"""
    
    def __init__(self):
        self.analyzer = HandAnalyzer()
    
    def analyze_completed_hand(self, hand_data: Dict) -> Dict:
        """Проанализировать завершенную раздачу"""
        analysis = {
            "rating": 0,
            "mistakes": [],
            "good_plays": [],
            "ev_calculation": 0,
            "improvement_tips": []
        }
        
        # Анализ префлопа
        preflop_analysis = self._analyze_preflop_decision(hand_data)
        analysis.update(preflop_analysis)
        
        # Анализ постфлопа
        postflop_analysis = self._analyze_postflop_decisions(hand_data)
        analysis.update(postflop_analysis)
        
        # Итоговый рейтинг
        analysis["rating"] = self._calculate_hand_rating(analysis)
        
        return analysis
    
    def _analyze_preflop_decision(self, hand_data: Dict) -> Dict:
        """Анализ префлоп решений"""
        result = {"preflop_mistakes": [], "preflop_good": []}
        
        # Проверка силы руки и принятого решения
        hand_strength = hand_data.get("hand_strength", 0.5)
        action = hand_data.get("preflop_action", "")
        position = hand_data.get("position", "")
        
        if hand_strength < 0.4 and action == "raise":
            result["preflop_mistakes"].append("Рейз со слабой рукой")
        elif hand_strength > 0.7 and action == "fold":
            result["preflop_mistakes"].append("Фолд с премиум рукой")
        elif hand_strength > 0.6 and action == "raise":
            result["preflop_good"].append("Агрессивная игра с сильной рукой")
        
        return result
    
    def _analyze_postflop_decisions(self, hand_data: Dict) -> Dict:
        """Анализ постфлоп решений"""
        return {
            "postflop_mistakes": [],
            "postflop_good": [],
            "ev_analysis": "Базовый анализ EV"
        }
    
    def _calculate_hand_rating(self, analysis: Dict) -> int:
        """Рассчитать рейтинг раздачи (1-10)"""
        base_rating = 7
        mistakes = len(analysis.get("preflop_mistakes", [])) + len(analysis.get("postflop_mistakes", []))
        good_plays = len(analysis.get("preflop_good", [])) + len(analysis.get("postflop_good", []))
        
        rating = base_rating - mistakes + good_plays
        return max(1, min(10, rating))

# Глобальный экземпляр анализатора
hand_analyzer = HandAnalyzer()
history_analyzer = HandHistoryAnalyzer()