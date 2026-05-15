import torch
import torch.nn as nn
import torch.nn.functional as F


class OnlineHardTripletLoss(nn.Module):
    """
    Zamiast losować trójki z DataLoadera, liczymy wszystkie możliwe
    pary w batchu i wybieramy najtrudniejsze.

    Wymaga żeby batch zawierał wiele przykładów PER KLASA —
    użyj BalancedBatchSampler zamiast zwykłego DataLoadera.
    """
    def __init__(self, margin=0.3):
        super().__init__()
        # WAŻNE: margin 0.3 zamiast 1.0 — przy z-score embeddingi
        # są już w podobnej skali, duży margin jest zbędny
        self.margin = margin

    def forward(self, embeddings: torch.Tensor,
                labels: torch.Tensor) -> torch.Tensor:
        """
        embeddings: (B, hidden_dim) — last_state z LSTM
        labels:     (B,)            — id klasy
        """
        # macierz wszystkich odległości parami (B, B)
        dist_matrix = self._pairwise_distances(embeddings)

        loss = self._batch_hard_triplet_loss(dist_matrix, labels)
        return loss

    def _pairwise_distances(self, embeddings):
        """Macierz odległości euklidesowych między wszystkimi parami."""
        dot   = torch.mm(embeddings, embeddings.t())
        sq    = dot.diag().unsqueeze(1)
        dists = sq + sq.t() - 2.0 * dot
        # clamp usuwa ujemne wartości przez błędy numeryczne
        return torch.clamp(dists, min=1e-12).sqrt()

    def _batch_hard_triplet_loss(self, dist_matrix, labels):
        B = labels.size(0)

        # maski: które pary to ten sam gest, które to różne
        labels_eq  = labels.unsqueeze(0) == labels.unsqueeze(1)  # (B, B)
        labels_neq = ~labels_eq

        # ignoruj przekątną (porównanie ze sobą)
        eye = torch.eye(B, dtype=torch.bool, device=labels.device)
        labels_eq = labels_eq & ~eye

        # HARD POSITIVE: dla każdego anchor — najdalszy positive
        # (najtrudniejsza para tego samego gestu)
        hardest_pos = (dist_matrix * labels_eq.float()).max(dim=1).values

        # HARD NEGATIVE: dla każdego anchor — najbliższy negative
        # (najtrudniejsza para różnego gestu)
        # ustaw duże wartości dla par tego samego gestu żeby nie były wybrane
        inf_mask  = labels_eq.float() * 1e9
        hardest_neg = (dist_matrix + inf_mask).min(dim=1).values

        loss = torch.clamp(hardest_pos - hardest_neg + self.margin, min=0)
        return loss.mean()