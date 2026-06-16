import torch
import torch.nn as nn


import torch
import torch.nn as nn


class TransformerEncoder_model(nn.Module):
    def __init__(
        self,
        input_dim=144,
        hidden_dim=64,
        num_layers=3,
        dropout=0.3,
    ):
        super().__init__()


        weights = torch.ones(input_dim)
        weights[0:18] = 1.0 
        weights[18:81] = 3.0  
        weights[81:144] = 3.0 
        self.register_buffer("input_weights", weights)

        self.input_projection = nn.Linear(input_dim, hidden_dim)

        self.nhead = 8
        for nh in [8, 4, 2, 1]:
            if hidden_dim % nh == 0:
                self.nhead = nh
                break

        self.pos_embedding = nn.Parameter(torch.zeros(1, 1000, hidden_dim))
        nn.init.normal_(self.pos_embedding, std=0.02)

        # Blok Transformera
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
        embedding_dim=64

        self.embedding_head = nn.Sequential(
            nn.Linear(3*hidden_dim, 2*hidden_dim),
            nn.GELU(),
            nn.Linear(2*hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, embedding_dim),
        )

        self.decoder = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor):
        x = x * self.input_weights
        x = self.input_projection(x)

        T = x.size(1)
        x = x + self.pos_embedding[:, :T, :]

        sequence = self.transformer(x)  

        reconstructed = self.decoder(sequence) 

        pooled_mean = sequence.mean(dim=1)  
        pooled_min, _ = sequence.min(dim=1)  
        pooled_max, _ = sequence.max(dim=1)  

        embedding_combined = torch.cat((pooled_mean, pooled_min, pooled_max), dim=1)

        embedding = self.embedding_head(embedding_combined)

        return reconstructed, embedding
