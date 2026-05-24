import random
import numpy as np
from torch.utils.data import Sampler


class BalancedBatchSampler(Sampler):
    """
    Każdy batch zawiera P klas × K przykładów = B próbek.
    
    Dla 32 gestów: P=8 klas, K=4 przykłady → batch=32
    
    WAŻNE: P musi być <= liczba klas, K <= min nagrań na gest
    """
    def __init__(self, labels, P=8, K=4):
        self.P = P  # klas per batch
        self.K = K  # przykładów per klasa

        # grupuj indeksy po klasie
        self.by_label = {}
        for idx, label in enumerate(labels):
            if label not in self.by_label:
                self.by_label[label] = []
            self.by_label[label].append(idx)

        self.all_labels = list(self.by_label.keys())
        # ile batchów na epokę
        self.n_batches  = len(labels) // (P * K)

    def __iter__(self):
        for _ in range(self.n_batches):
            batch = []
            # losuj P różnych klas
            chosen_labels = random.sample(self.all_labels, self.P)
            for label in chosen_labels:
                # losuj K przykładów z każdej klasy
                indices = random.choices(self.by_label[label], k=self.K)
                batch.extend(indices)
            yield batch

    def __len__(self):
        return self.n_batches