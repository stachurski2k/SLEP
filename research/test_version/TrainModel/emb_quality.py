import torch
import torch.nn.functional as F


def pairwise_distances(embeddings: torch.Tensor) -> torch.Tensor:
    dot = embeddings @ embeddings.t()
    sq = dot.diag()
    distances = sq.unsqueeze(1) + sq.unsqueeze(0) - 2.0 * dot
    return distances.clamp(min=1e-12).sqrt()


def distance_stats(distances: torch.Tensor, labels: torch.Tensor):
    same = labels.unsqueeze(0) == labels.unsqueeze(1)
    eye  = torch.eye(len(labels), dtype=torch.bool, device=labels.device)

    pos_mask = same & ~eye
    neg_mask = ~same

    d_pos = distances[pos_mask].mean().item() if pos_mask.any() else float("nan")
    d_neg = distances[neg_mask].mean().item() if neg_mask.any() else float("nan")

    return d_pos, d_neg


def embedding_distances(model, loader, device):
    total_pos = 0.0
    total_neg = 0.0
    count_pos = 0
    count_neg = 0

    with torch.no_grad():
        for sequences, labels in loader:
            embeddings = model(sequences.to(device))[0]
            embeddings = F.normalize(embeddings, p=2, dim=1)

            d_pos, d_neg = distance_stats(pairwise_distances(embeddings), labels.to(device))

            if d_pos == d_pos:
                total_pos += d_pos
                count_pos += 1
            if d_neg == d_neg:
                total_neg += d_neg
                count_neg += 1

    d_pos_avg = total_pos / count_pos if count_pos > 0 else float("nan")
    d_neg_avg = total_neg / count_neg if count_neg > 0 else float("nan")
    
    return {"d_pos": d_pos_avg, "d_neg": d_neg_avg, "diff": d_neg_avg - d_pos_avg}
