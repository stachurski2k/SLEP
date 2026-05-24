import torch
import torch.nn as nn


class LSTMEncoder(nn.Module):
    def __init__(self, input_dim=126, hidden_dim=64, num_layers=3, dropout=0.3):
        super().__init__()

        # wagi wejściowe — ręce ważniejsze
        weights = torch.ones(input_dim)
        weights[18:81]   = 3.0   # lewa ręka
        weights[81:144]  = 3.0   # prawa ręka
        weights[0:18]    = 1.0   # pose
        weights[144:204] = 0.5   # twarz
        self.register_buffer("input_weights", weights)

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

    def forward(self, x: torch.Tensor):
        # x: (B, T, input_dim)
        output, (h_n, _) = self.lstm(x)

        sequence   = output          # (B, T, hidden_dim)   → DTW
        last_state = h_n[-1]         # (B, hidden_dim)      → FAISS

        return sequence, last_state