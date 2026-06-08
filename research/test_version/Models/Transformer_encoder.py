import torch
import torch.nn as nn


class TransformerEncoder(nn.Module):
    def __init__(self, input_dim=144, hidden_dim=64, num_layers=3, dropout=0.3):
        super().__init__()

        # input weights (identical to LSTMEncoder)
        weights = torch.ones(input_dim)
        weights[0:18]   = 1.0   # pose
        weights[18:81]  = 3.0   # left hand
        weights[81:144] = 3.0   # right hand
        self.register_buffer("input_weights", weights)

        # Projection from input_dim to hidden_dim
        self.input_projection = nn.Linear(input_dim, hidden_dim)

        # Dynamically determine the head count that divides hidden_dim perfectly
        self.nhead = 8
        for nh in [8, 4, 2, 1]:
            if hidden_dim % nh == 0:
                self.nhead = nh
                break

        # Learnable positional embeddings (supports sequence lengths up to 1000)
        self.pos_embedding = nn.Parameter(torch.zeros(1, 1000, hidden_dim))
        nn.init.normal_(self.pos_embedding, std=0.02)

        # Transformer encoder block
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=self.nhead,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

    def forward(self, x: torch.Tensor):
        # Apply input weights
        x = x * self.input_weights

        # Project to hidden_dim
        x = self.input_projection(x)

        # Add positional embedding up to sequence length T
        T = x.size(1)
        x = x + self.pos_embedding[:, :T, :]

        # Forward pass through the Transformer
        sequence = self.transformer(x)  # Shape: (B, T, hidden_dim)

        # Global average pooling to compute the overall sequence embedding
        last_state = sequence.mean(dim=1)  # Shape: (B, hidden_dim)

        return sequence, last_state
