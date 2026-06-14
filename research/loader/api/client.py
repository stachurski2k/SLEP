import torch
from torch.utils.data import DataLoader
from pathlib import Path
from typing import Union, Callable, Optional
import urllib.request
import json
import time
import zipfile
import io

from landmark_dataset import get_landmark_dataloader

def download_and_extract_dataset(dataset_id: int, 
                                 backend_url: str = "http://localhost:5000", 
                                 dest_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Queries/triggers the backend to export the dataset as a ZIP file, downloads it,
    and extracts it to the local directory.
    
    Args:
        dataset_id: The ID of the dataset to download.
        backend_url: The base URL of the FastAPI backend.
        dest_dir: Optional destination directory. Defaults to research/loader/data/dataset_{id}.
    Returns:
        The Path to the directory containing the extracted .npy files.
    """
    if dest_dir is None:
        dest_dir = Path(__file__).parent.parent / "data" / f"dataset_{dataset_id}"
    dest_path = Path(dest_dir)
    
    # 1. Look for an existing exported dataset for this dataset ID
    print(f"Checking for existing exports of dataset {dataset_id}...")
    try:
        req = urllib.request.Request(f"{backend_url}/api/v1/exported-datasets/?limit=100")
        with urllib.request.urlopen(req) as response:
            exports = json.loads(response.read().decode())
        
        matching_exports = [e for e in exports if e.get("original_dataset_id") == dataset_id]
    except Exception as e:
        print(f"Failed to query exported datasets: {e}. Will attempt to trigger new job.")
        matching_exports = []
    
    exported_dataset_id = None
    if matching_exports:
        matching_exports.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        exported_dataset_id = matching_exports[0]["id"]
        s3_key = matching_exports[0]["filepath"]
        print(f"Found existing exported dataset ID: {exported_dataset_id} (S3 Key: {s3_key})")
    else:
        # 2. Trigger a new export job
        print(f"No existing exports found. Triggering new export job for dataset {dataset_id}...")
        post_data = json.dumps({"original_dataset_id": dataset_id}).encode('utf-8')
        req = urllib.request.Request(
            f"{backend_url}/api/v1/export-dataset-jobs/",
            data=post_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            job = json.loads(response.read().decode())
        
        job_id = job["id"]
        print(f"Export job triggered. Job ID: {job_id}. Polling status...")
        
        # 3. Poll job status until done
        while True:
            poll_req = urllib.request.Request(f"{backend_url}/api/v1/export-dataset-jobs/{job_id}")
            with urllib.request.urlopen(poll_req) as response:
                job_status = json.loads(response.read().decode())
            
            status = job_status.get("status")
            if status == "done":
                exported_dataset_id = job_status.get("exported_dataset_id")
                print(f"Export job completed! Exported Dataset ID: {exported_dataset_id}")
                break
            elif status == "error":
                raise RuntimeError(f"Export dataset job failed: {job_status.get('error_message')}")
            elif status in ("in_queue", "processing"):
                time.sleep(2)
            else:
                raise RuntimeError(f"Unexpected job status: {status}")
        
        req = urllib.request.Request(f"{backend_url}/api/v1/exported-datasets/{exported_dataset_id}")
        with urllib.request.urlopen(req) as response:
            exported_dataset = json.loads(response.read().decode())
        s3_key = exported_dataset["filepath"]

    # 4. Request presigned download URL
    print(f"Requesting presigned download URL for {s3_key}...")
    url_data = json.dumps({"s3_key": s3_key}).encode('utf-8')
    req = urllib.request.Request(
        f"{backend_url}/api/v1/s3/download-url",
        data=url_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        url_resp = json.loads(response.read().decode())
    download_url = url_resp["url"]
    
    # Redirect localhost to internal S3 domain when running inside Docker container
    docker_redirect = False
    if "localhost:9000" in download_url:
        import socket
        try:
            socket.gethostbyname("s3")
            download_url = download_url.replace("localhost:9000", "s3:9000")
            docker_redirect = True
            print(f"Internal Docker S3 redirect: rewritten download URL to: {download_url}")
        except socket.gaierror:
            pass
            
    # 5. Download zip file bytes
    print(f"Downloading dataset archive...")
    req = urllib.request.Request(download_url)
    if docker_redirect:
        req.add_header("Host", "localhost:9000")
        
    with urllib.request.urlopen(req) as response:
        zip_bytes = response.read()
    
    # 6. Extract zip archive to dest_dir
    print(f"Extracting archive to {dest_path.resolve()}...")
    dest_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_ref:
        zip_ref.extractall(dest_path)
        
    print("Dataset successfully downloaded and extracted.")
    return dest_path


def get_backend_dataloader(dataset_id: int,
                           backend_url: str = "http://localhost:5000",
                           dest_dir: Optional[Union[str, Path]] = None,
                           batch_size: int = 32,
                           shuffle: bool = True,
                           num_frames: Optional[int] = None,
                           transform: Optional[Callable] = None,
                           num_workers: int = 0) -> DataLoader:
    """
    Downloads and extracts a dataset from the backend API, reads the extracted 
    files, and constructs a PyTorch DataLoader.
    """
    extracted_dir = download_and_extract_dataset(dataset_id, backend_url, dest_dir)
    
    from utils.get_file_paths import get_file_paths
    file_paths, labels = get_file_paths(extracted_dir)
    
    print(f"Creating DataLoader with {len(file_paths)} items...")
    return get_landmark_dataloader(
        file_paths=file_paths,
        labels=labels,
        batch_size=batch_size,
        shuffle=shuffle,
        num_frames=num_frames,
        transform=transform,
        num_workers=num_workers
    )
