# app/ml/poker_nn.py
import torch
import torch.nn as nn

class PokerNN(nn.Module):
    def __init__(self, input_size=128, hidden_size=256, output_size=4):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, output_size)  # [FOLD, CHECK, CALL, RAISE]
        )
    
    def forward(self, x):
        return self.network(x)