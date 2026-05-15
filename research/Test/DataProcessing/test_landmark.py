import numpy as np

seq = np.load("Features/FOOTBALL/7260097842820659-FOOTBALL.npy")

# wektory per część ciała
pose  = seq[:, 0:18]     # 6 punktów × 3
left  = seq[:, 18:81]    # lewa ręka
right = seq[:, 81:144]   # prawa ręka
face  = seq[:, 144:204]  # twarz

print("NaN per część ciała:")
print(f"  pose:  {np.isnan(pose).any(axis=1).mean():.0%} klatek")
print(f"  lewa:  {np.isnan(left).any(axis=1).mean():.0%} klatek")
print(f"  prawa: {np.isnan(right).any(axis=1).mean():.0%} klatek")
print(f"  twarz: {np.isnan(face).any(axis=1).mean():.0%} klatek")