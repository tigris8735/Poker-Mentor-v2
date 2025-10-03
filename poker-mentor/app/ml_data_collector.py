# Создаем app/ml_data_collector.py
class MLDataCollector:
    def __init__(self):
        self.training_data = []
    
    def record_decision_point(self, game_state: Dict, action: str, ev: float):
        """Запись точки принятия решения для ML"""
        features = self._extract_features(game_state)
        self.training_data.append({
            'features': features,
            'action': action,
            'ev': ev,
            'timestamp': datetime.now()
        })
    
    def _extract_features(self, game_state: Dict) -> List[float]:
        """Извлечение фич для ML модели"""
        return [
            game_state['hand_strength'],
            game_state['position_value'],
            game_state['stack_ratio'],
            game_state['pot_odds'],
            # ... другие фичи
        ]