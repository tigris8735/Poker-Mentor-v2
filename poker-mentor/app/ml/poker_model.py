import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import logging

logger = logging.getLogger(__name__)

class PokerPredictor(nn.Module):
    """Нейросеть для предсказания покерных решений"""
    
    def __init__(self, input_dim=47, hidden_dim=128, output_dim=4):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(), 
            nn.BatchNorm1d(hidden_dim // 2),
            nn.Dropout(0.3),
            
            nn.Linear(hidden_dim // 2, hidden_dim // 4),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim // 4),
            nn.Dropout(0.2),
            
            nn.Linear(hidden_dim // 4, output_dim)
        )
        
        # Инициализация весов
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Инициализация весов сети"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, x):
        return self.network(x)
    
    def predict_action(self, features: list) -> dict:
        """Предсказание действия на основе фич"""
        try:
            self.eval()  # Режим оценки
            
            if len(features) != self.input_dim:
                raise ValueError(f"Expected {self.input_dim} features, got {len(features)}")
            
            # Конвертация в tensor
            features_tensor = torch.FloatTensor(features).unsqueeze(0)
            
            # Предсказание
            with torch.no_grad():
                output = self.forward(features_tensor)
                probabilities = torch.softmax(output, dim=1)
                confidence = torch.max(probabilities).item()
                
            action_idx = torch.argmax(output, dim=1).item()
            action_map = {0: 'fold', 1: 'check', 2: 'call', 3: 'raise'}
            
            return {
                'action': action_map.get(action_idx, 'fold'),
                'confidence': confidence,
                'probabilities': probabilities.squeeze().tolist()
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {'action': 'fold', 'confidence': 0.0, 'error': str(e)}

# Утилита для создания модели
def create_poker_model() -> PokerPredictor:
    """Создание и инициализация модели"""
    model = PokerPredictor()
    logger.info("Poker model created successfully")
    return model