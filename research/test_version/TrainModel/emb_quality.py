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

    totals = {"pos": 0.0, "neg": 0.0, "n": 0}

    with torch.no_grad():
        for sequences, labels in loader:
            embeddings = model(sequences.to(device))[0]
            embeddings = F.normalize(embeddings, p=2, dim=1)

            d_pos, d_neg = distance_stats(pairwise_distances(embeddings), labels.to(device))

            totals["pos"] += d_pos
            totals["neg"] += d_neg
            totals["n"]   += 1

    n = totals["n"]
    return {"d_pos": totals["pos"] / n, "d_neg": totals["neg"] / n, "diff": (totals["neg"] - totals["pos"]) / n}