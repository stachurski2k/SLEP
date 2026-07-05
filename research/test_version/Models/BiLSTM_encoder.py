import torch
import torch.nn as nn


class BiLSTMEncoder(nn.Module):
    def __init__(self, input_dim=144, hidden_dim=128, num_layers=2, dropout=0.4):
        super().__init__()

        weights = torch.ones(input_dim)
        weights[18:81] = 3.0
        weights[81:144] = 3.0
        self.register_buffer("input_weights", weights)

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=True
        )
        embedding_dim=64

        self.embedding_head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, embedding_dim)
        )

        self.decoder = nn.Linear(hidden_dim * 2, input_dim)

    def forward(self, x):
        self.lstm.flatten_parameters()

        x = x * self.input_weights

        output, (h_n, c_n) = self.lstm(x)

        pooled = output.mean(dim=1)
        embedding = self.embedding_head(pooled)

        reconstructed = self.decoder(output)

        return embedding, reconstructed
