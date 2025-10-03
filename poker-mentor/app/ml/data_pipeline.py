import logging
import json
from datetime import datetime
from typing import List, Dict, Any
import sqlite3

logger = logging.getLogger(__name__)

class DataPipeline:
    """Пайплайн для сбора и обработки данных ML"""
    
    def __init__(self, db_path: str = "poker_mentor.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Инициализация таблицы ML данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                features TEXT NOT NULL,
                action INTEGER NOT NULL,
                result REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                game_context TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("ML database initialized")
    
    def record_decision(self, user_id: int, game_state: Dict[str, Any], 
                       action: str, result: float, context: str = ""):
        """Запись точки принятия решения"""
        try:
            features = self._extract_features(game_state)
            action_idx = self._action_to_index(action)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ml_training_data 
                (features, action, result, user_id, game_context)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                json.dumps(features),
                action_idx,
                result,
                user_id,
                context
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"Recorded ML data for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording ML data: {e}")
    
    def _extract_features(self, game_state: Dict[str, Any]) -> List[float]:
        """Извлечение 47 фич из состояния игры"""
        features = []
        
        # 1. Сила руки (0-1)
        features.append(game_state.get('hand_strength', 0.5))
        
        # 2. Позиционные фичи (4 фичи)
        position = game_state.get('position', 'middle')
        position_map = {'early': 0.0, 'middle': 0.5, 'late': 1.0, 'blinds': 0.25}
        features.append(position_map.get(position, 0.5))
        
        # 3. Фичи стека и банка (5 фич)
        features.append(game_state.get('stack_ratio', 1.0))
        features.append(game_state.get('pot_ratio', 0.1))
        features.append(game_state.get('effective_stack', 50.0))
        
        # 4. Стадия игры (4 фичи)
        street = game_state.get('street', 'preflop')
        street_map = {'preflop': 0.0, 'flop': 0.33, 'turn': 0.66, 'river': 1.0}
        features.append(street_map.get(street, 0.0))
        
        # 5. Стиль оппонента (4 фичи)
        features.append(game_state.get('opponent_aggression', 0.5))
        features.append(game_state.get('opponent_tightness', 0.5))
        
        # 6. История действий (10 фич)
        # ... остальные фичи пока заполняем нулями
        
        # Добиваем до 47 фич нулями (временная мера)
        while len(features) < 47:
            features.append(0.0)
            
        return features[:47]  # Обрезаем до 47 фич
    
    def _action_to_index(self, action: str) -> int:
        """Конвертация действия в числовой индекс"""
        action_map = {
            'fold': 0,
            'check': 1, 
            'call': 2,
            'raise': 3
        }
        return action_map.get(action.lower(), 0)
    
    def get_training_data(self, limit: int = 10000) -> tuple:
        """Получение данных для обучения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT features, action, result FROM ml_training_data 
            ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        
        data = cursor.fetchall()
        conn.close()
        
        features = []
        actions = []
        results = []
        
        for row in data:
            features.append(json.loads(row[0]))
            actions.append(row[1])
            results.append(row[2])
        
        return features, actions, results

# Глобальный экземпляр
ml_data_pipeline = DataPipeline()