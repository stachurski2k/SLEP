from mediapipe.python.solutions import selfie_segmentation
import random
from torch.utils.data import Sampler


class BalancedBatchSampler(Sampler):

    def __init__(self, labels, P=4, K=8, num_batches=None):

        self.P = P  # number of classes per batch
        self.K = K  # number of samples per class

        # group index by classes
        self.class_to_indices = {}

        for idx, label in enumerate(labels):

            if label not in self.class_to_indices:
                self.class_to_indices[label] = []

            self.class_to_indices[label].append(idx)

        # list of all classes
        self.classes = list(self.class_to_indices.keys())

        # number of baches per epoch
        total_samples = len(labels)
        batch_size = P * K
        
        if num_batches is not None:
            self.num_batches = num_batches
        else:
            self.num_batches = max(1, total_samples // batch_size)

    def __iter__(self):

        for _ in range(self.num_batches):

            batch_indices = []

            # P classes per batch
            chosen_classes = random.sample(self.classes, self.P)

            # K samples from each class
            for cls in chosen_classes:

                available_indices = self.class_to_indices[cls]

                if len(available_indices) >= self.K:
                    chosen_indices = random.sample(available_indices, k=self.K)
                else:
                    chosen_indices = random.choices(available_indices, k=self.K)

                batch_indices.extend(chosen_indices)

            yield batch_indices

    def __len__(self):
        return self.num_batches