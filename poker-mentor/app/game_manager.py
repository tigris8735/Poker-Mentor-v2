import logging
from app.poker_engine import PokerGame, Action
from app.ai_opponents import AIFactory
from app.ml.data_pipeline import ml_data_pipeline

logger = logging.getLogger(__name__)

class GameManager:
    """Управление игровыми сессиями"""
    
    def __init__(self):
        self.active_games = {}
        self.data_pipeline = ml_data_pipeline

    
    
    def create_game(self, user_id: str, ai_type: str = "fish") -> PokerGame:
        """Создать новую игру"""
        ai_opponent = AIFactory.create_ai(ai_type)
        
        game = PokerGame([f"user_{user_id}", ai_opponent.name])
        game.ai_opponent = ai_opponent
        game.start_hand()
        game.post_blinds()
        
        self.active_games[user_id] = game
        logger.info(f"Создана новая игра для пользователя {user_id} с AI {ai_type}")
        
        return game
    
    def get_game(self, user_id: str) -> PokerGame:
        """Получить активную игру пользователя"""
        return self.active_games.get(user_id)
    
    def end_game(self, user_id: str):
        """Завершить игру"""
        if user_id in self.active_games:
            del self.active_games[user_id]
            logger.info(f"Игра пользователя {user_id} завершена")
    
    def process_player_action(self, user_id: str, action: str, amount: int = 0) -> dict:
        """Обработать действие игрока"""
        game = self.get_game(user_id)
        if not game:
            return {"error": "Игра не найдена"}
        
        player = f"user_{user_id}"
        result = {
            "player_action": action,
            "player_amount": amount,
            "ai_action": None,
            "ai_amount": 0,
            "pot": game.pot,
            "player_stack": game.player_stacks[player],
            "community_cards": game.community_cards.copy(),
            "game_continues": True
        }
        
        # Обрабатываем действие игрока
        if action == "fold":
            game.player_stacks[player] -= 0
            result["game_continues"] = False
            result["message"] = "❌ Вы сбросили карты."
            
        elif action == "call":
            call_amount = game.current_bet
            game.player_stacks[player] -= call_amount
            game.pot += call_amount
            result["player_amount"] = call_amount
            result["message"] = f"📥 Вы поставили {call_amount} BB"
            
        elif action == "check":
            game.player_stacks[player] -= 0
            result["message"] = "⚖️ Вы пропустили ход"
            
        elif action == "raise":
            game.player_stacks[player] -= amount
            game.pot += amount
            game.current_bet = amount
            result["message"] = f"📤 Вы поставили рейз {amount} BB"
        
        try:
            # Собираем данные для ML обучения
            game_state = self._extract_ml_features(user_id, action, result, game)
            ml_data_pipeline.record_decision(
                user_id=int(user_id),
                game_state=game_state,
                action=action,
                result=0.0,  # Пока заглушка для EV
                context=f"game_action_{action}"
            )
            logger.debug(f"Recorded ML data for user {user_id}, action: {action}")
        except Exception as e:
            logger.error(f"ML data collection error: {e}")

        # Ход AI
        if result["game_continues"]:
            ai_action, ai_amount = self._process_ai_turn(game)
            result["ai_action"] = ai_action
            result["ai_amount"] = ai_amount
            result["ai_message"] = self._get_ai_action_text(ai_action, ai_amount)
            
            # Обновляем состояние после хода AI
            result["pot"] = game.pot
            result["player_stack"] = game.player_stacks[player]
        
        # Проверяем продолжение игры
        if result["game_continues"]:
            result["game_continues"] = self._advance_game_street(game)
            if not result["game_continues"]:
                # Шоудаун
                winners = game.get_winner()
                result["winner"] = "Вы" if 'user' in winners[0] else "AI"
                result["winning_hand"] = game.evaluate_showdown()[winners[0]][0].name
        
        return result
    
    def _process_ai_turn(self, game: PokerGame) -> tuple:
        """Обработать ход AI"""
        ai_action, ai_amount = game.ai_opponent.decide_action(game, game.ai_opponent.name)
        
        if ai_action == Action.FOLD:
            game.player_stacks[game.ai_opponent.name] -= 0
        elif ai_action == Action.CHECK:
            game.player_stacks[game.ai_opponent.name] -= 0
        elif ai_action == Action.CALL:
            game.player_stacks[game.ai_opponent.name] -= ai_amount
            game.pot += ai_amount
        elif ai_action == Action.RAISE:
            game.player_stacks[game.ai_opponent.name] -= ai_amount
            game.pot += ai_amount
            game.current_bet = ai_amount
        
        return ai_action.value, ai_amount
    
    def _get_ai_action_text(self, ai_action: str, ai_amount: int) -> str:
        """Получить текстовое описание действия AI"""
        actions = {
            "fold": "🤖 AI: фолд",
            "check": "🤖 AI: чек", 
            "call": f"🤖 AI: колл {ai_amount} BB",
            "raise": f"🤖 AI: рейз {ai_amount} BB"
        }
        return actions.get(ai_action, "🤖 AI: неизвестное действие")
    
    def _advance_game_street(self, game: PokerGame) -> bool:
        """Перейти на следующую улицу игры"""
        if len(game.community_cards) == 0:
            game.deal_flop()
            return True
        elif len(game.community_cards) == 3:
            game.deal_turn()
            return True
        elif len(game.community_cards) == 4:
            game.deal_river()
            return True
        else:
            # Игра завершена
            return False
    
    def get_game_state(self, user_id: str) -> dict:
        """Получить текущее состояние игры"""
        game = self.get_game(user_id)
        if not game:
            return None
        
        player = f"user_{user_id}"
        return {
            "user_cards": game.player_cards[player],
            "user_stack": game.player_stacks[player],
            "pot": game.pot,
            "current_bet": game.current_bet,
            "community_cards": game.community_cards,
            "ai_name": game.ai_opponent.name if hasattr(game, 'ai_opponent') else "AI"
        }
    
    def _extract_ml_features(self, user_id: str, action: str, result: dict, game: PokerGame) -> dict:
        """Извлечение фич для ML из состояния игры"""
        try:
            player = f"user_{user_id}"
            
            # Определяем текущую улицу по количеству карт
            street = "preflop"
            if len(game.community_cards) == 3:
                street = "flop"
            elif len(game.community_cards) == 4:
                street = "turn" 
            elif len(game.community_cards) == 5:
                street = "river"
            
            # Базовые фичи для ML
            features = {
                'hand_strength': self._calculate_hand_strength(game, user_id),
                'position': 'middle',  # Временная заглушка
                'stack_ratio': game.player_stacks[player] / 100.0,  # Относительно стартового стека 100
                'pot_ratio': game.pot / 100.0,
                'street': street,
                'action_taken': action,
                'current_bet_ratio': game.current_bet / 100.0,
            }
            
            # Добавляем информацию об оппоненте если есть
            if hasattr(game, 'ai_opponent'):
                features.update({
                    'opponent_aggression': game.ai_opponent.aggression,
                    'opponent_tightness': game.ai_opponent.tightness,
                    'opponent_type': game.ai_opponent.name.lower()
                })
            else:
                features.update({
                    'opponent_aggression': 0.5,
                    'opponent_tightness': 0.5,
                    'opponent_type': 'unknown'
                })
                
            return features
            
        except Exception as e:
            logger.error(f"Error extracting ML features: {e}")
            return {}
    
    def _calculate_hand_strength(self, game: PokerGame, user_id: str) -> float:
        """Упрощенный расчет силы руки (0-1)"""
        try:
            player = f"user_{user_id}"
            cards = game.player_cards[player]
            
            if len(cards) != 2:
                return 0.5
                
            # Простая эвристика для демонстрации
            rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                          '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
            
            card1, card2 = cards
            rank1_val = rank_values.get(card1.rank.value, 7)
            rank2_val = rank_values.get(card2.rank.value, 7)
            
            # Пара
            if card1.rank == card2.rank:
                return min(0.95, rank1_val / 14.0 + 0.3)
            
            # suited
            suited_bonus = 0.1 if card1.suit == card2.suit else 0
            
            # Коннекторы
            gap = abs(rank1_val - rank2_val)
            connector_bonus = max(0, 0.1 - gap * 0.02)
            
            base_strength = (max(rank1_val, rank2_val) / 14.0) * 0.6
            
            return min(0.9, base_strength + suited_bonus + connector_bonus)
            
        except Exception as e:
            logger.error(f"Error calculating hand strength: {e}")
            return 0.5