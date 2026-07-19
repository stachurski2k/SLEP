from pathlib import Path
import numpy as np

video_path = "Features/MORNING/410755409280005-MORNING.npy"
seq = np.load(video_path)

POSE = slice(0, 18)
LEFT_HAND  = slice(18, 81)
RIGHT_HAND = slice(81, 144)

pose_nan = np.isnan(seq[:,POSE]).any(axis=1)
left_nan  = np.isnan(seq[:, LEFT_HAND]).any(axis=1)
right_nan = np.isnan(seq[:, RIGHT_HAND]).any(axis=1)

both_nan  = left_nan & right_nan
print(f"Video path:             {video_path}")
print(f"{'Total frames:':<24} {len(seq)}")
print(f"{'Pose NaN:':<20} {pose_nan.sum():>6} {pose_nan.mean():>10.0%}")
print(f"{'Left hand NaN:':<20} {left_nan.sum():>6} {left_nan.mean():>10.0%}")
print(f"{'Right hand NaN:':<20} {right_nan.sum():>6} {right_nan.mean():>10.0%}")
print(f"{'Both hands NaN:':<20} {both_nan.sum():>6} {both_nan.mean():>10.0%}")
print(f"Frame index (both NaN): {np.where(both_nan)[0].tolist()}")

point_names = (
    [f"pose_{i}" for i in range(6)]                                # pose (6)
  + [f"left_hand_{i}" for i in range(21)]                          # lewa ręka (21)
  + [f"right_hand_{i}" for i in range(21)]                         # prawa ręka (21)
)

output_path = Path(__file__).parent / "diagnose_video_result.txt"\

with open(output_path, "w", encoding="utf-8") as f:
    f.write(f"{'Video path:':<25} {video_path}\n")
    f.write(f"{'Total frames:':<25} {len(seq)}\n")
    f.write(f"{'Pose NaN:':<25} {pose_nan.sum():>6} {pose_nan.mean():>10.0%}\n")
    f.write(f"{'Left hand NaN:':<25} {left_nan.sum():>6} {left_nan.mean():>10.0%}\n")
    f.write(f"{'Right hand NaN:':<25} {right_nan.sum():>6} {right_nan.mean():>10.0%}\n")
    f.write(f"{'Both hands NaN:':<25} {both_nan.sum():>6} {both_nan.mean():>10.0%}\n")
    f.write(f"Frame index (both NaN): {np.where(both_nan)[0].tolist()}\n")
    for t, frame in enumerate(seq):
        f.write(f"\n── klatka {t} ──\n")
        for i, name in enumerate(point_names):
            x = frame[i*3]
            y = frame[i*3 + 1]
            z = frame[i*3 + 2]
            f.write(f"  {name:25s}  x={x:.4f}  y={y:.4f}  z={z:.4f}\n")
print(f"Saved in file {output_path}")
