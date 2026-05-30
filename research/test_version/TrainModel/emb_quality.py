import torch


def pairwise_distances(embeddings: torch.Tensor) -> torch.Tensor:
    dot = embeddings @ embeddings.t()                       # matrix product, result (B,B)
    diagonal = dot.diag().unsqueeze(1)                      # diagonal elements, shape (B,1)

    distances = diagonal + diagonal.t() - 2.0 * dot         # compute euclidean distances
    distances = torch.clamp(distances, min=1e-12).sqrt()    # clamp and sqrt

    return distances


def print_embedding_distances(model, loader, device, n_batches=3):
    model.eval()
    summaries = []

    with torch.no_grad():
        for batch_idx, (sequences, labels) in enumerate(loader):
            if batch_idx >= n_batches:
                break

            sequences = sequences.to(device)
            labels = labels.to(device)

            _, last_state = model(sequences)

            last_state = torch.nn.functional.normalize(last_state, p=2, dim=1)

            distances = pairwise_distances(last_state)

            same_label = labels.unsqueeze(0) == labels.unsqueeze(1)
            eye = torch.eye(len(labels), dtype=torch.bool, device=device)

            positive_mask = same_label & ~eye
            negative_mask = ~same_label

            if positive_mask.any():
                d_pos = distances[positive_mask].mean().item()
            else:
                d_pos = float("nan")

            if negative_mask.any():
                d_neg = distances[negative_mask].mean().item()
            else:
                d_neg = float("nan")

            print(
                f"batch {batch_idx + 1}: "
                f"d_pos={d_pos:.4f} | "
                f"d_neg={d_neg:.4f} | "
                f"diff={d_neg - d_pos:.4f}"
            )
            summaries.append((batch_idx + 1, d_pos, d_neg, d_neg - d_pos))

    model.train()
    return summaries
