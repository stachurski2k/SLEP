import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

LEFT_SHOULDER  = slice(0, 3)    
RIGHT_SHOULDER = slice(3, 6)    
LEFT_WRIST     = slice(12, 15)  
RIGHT_WRIST    = slice(15, 18)  

LEFT_HAND      = slice(18, 81) 
RIGHT_HAND     = slice(81, 144) 

def hands_activity(sequence: np.ndarray, threshold=0.15) -> np.ndarray:
    seq = sequence.copy()
    num_frames = len(seq)
    
    left_nan_frames = np.isnan(seq[:, LEFT_HAND]).all(axis=1)
    right_nan_frames = np.isnan(seq[:, RIGHT_HAND]).all(axis=1)
    
    left_valid_ratio = 1.0 - left_nan_frames.mean()
    right_valid_ratio = 1.0 - right_nan_frames.mean()
    
    # left hand
    if left_valid_ratio < threshold:
        for frame in range(num_frames):
            shoulder_pos = seq[frame, LEFT_SHOULDER]

            if np.isnan(shoulder_pos).any():
                shoulder_pos = np.zeros(3)
            seq[frame, LEFT_HAND] = np.tile(shoulder_pos, 21)
            
    # right hand
    if right_valid_ratio < threshold:
        for frame in range(num_frames):
            shoulder_pos = seq[frame, RIGHT_SHOULDER]
            if np.isnan(shoulder_pos).any():
                shoulder_pos = np.zeros(3)
            seq[frame, RIGHT_HAND] = np.tile(shoulder_pos, 21)
            
    return seq

def interpolate_position(sequence: np.ndarray) -> np.ndarray:
    seq = sequence.copy()
    num_frames = len(seq)
    indices = np.arange(num_frames)
    
    for dim in range(seq.shape[1]):
        col = seq[:, dim]           # single parameter of the landmark per frames
        nan_mask = np.isnan(col)
        
        if nan_mask.all():
            seq[:, dim] = 0.0
            continue
            
        if not nan_mask.any():
            continue
        
        # get frames with values
        valid_idx = indices[~nan_mask]
        valid_vals = col[~nan_mask]
        
        seq[:, dim] = np.interp(indices, valid_idx, valid_vals, left=valid_vals[0], right=valid_vals[-1])
        
    return seq

def remove_static_frames(sequence: np.ndarray, threshold=0.01) -> np.ndarray:
    # difference vectors of movement between frames
    frame_differences = np.diff(sequence, axis=0)
    # magnitude of movement difference vectors
    motion_magnitude = np.linalg.norm(frame_differences, axis=1)

    dynamic_idx = np.where(motion_magnitude > threshold)[0]
    
    if len(dynamic_idx) < 10:
        return sequence
        
    return sequence[dynamic_idx]

def Savitzky_Golay_filter(sequence: np.ndarray, window_length=5, polyorder=2) -> np.ndarray:
    if len(sequence) < window_length:
        return sequence
    
    smoothed = savgol_filter(sequence, window_length=window_length, polyorder=polyorder, axis=0)
    return smoothed

def normalization(sequence: np.ndarray) -> np.ndarray:
    normalized = sequence.copy().astype(np.float32)
    
    # translation (set center as midpoint between shoulders)
    left_sh = normalized[:, LEFT_SHOULDER]
    right_sh = normalized[:, RIGHT_SHOULDER]
    center = (left_sh + right_sh) / 2.0
    
    for i in range(0, normalized.shape[1], 3):
        normalized[:, i:i+3] -= center
        
    # scale (set distance between shoulders as 1)
    shoulder_dist = normalized[:, LEFT_SHOULDER] - normalized[:, RIGHT_SHOULDER]
    scale_factor = np.linalg.norm(shoulder_dist, axis=1, keepdims=True) + 1e-6
    
    normalized /= np.repeat(scale_factor, normalized.shape[1], axis=1)
    
    return normalized

def resample_sequence(sequence: np.ndarray, target_len=60) -> np.ndarray:
    num_frames, num_features = sequence.shape

    if num_frames == target_len:
        return sequence

    # Original timeline of the sequence.
    original_timestamps = np.linspace(0, 1, num_frames)

    # Target timeline after resampling.
    target_timestamps = np.linspace(0, 1, target_len)

    resampled = np.zeros((target_len, num_features), dtype=np.float32)

    for feature_idx in range(num_features):

        # Interpolation function for a single feature trajectory over time.
        interpolation_fn = interp1d(original_timestamps, sequence[:, feature_idx], kind="linear")

        resampled[:, feature_idx] = interpolation_fn(target_timestamps)

    return resampled

def preprocess(sequence: np.ndarray, target_len=60) -> np.ndarray:
    # check which hands are used in gesture
    seq = hands_activity(sequence)
    
    # interpolate values of missing landmarks
    seq = interpolate_position(seq)
    
    # use dynamic frames only
    seq = remove_static_frames(seq)
    
    # smooth sequence
    seq = Savitzky_Golay_filter(seq)

    # translate and scale
    seq = normalization(seq)
    
    # set a fixed number of frames
    seq = resample_sequence(seq, target_len)

    return seq