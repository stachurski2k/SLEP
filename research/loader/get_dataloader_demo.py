import os
import sys
from pathlib import Path
import torch

# 1. Dodanie bieżącego folderu roboczego do ścieżki importu
loader_dir = Path(__file__).parent
if str(loader_dir.resolve()) not in sys.path:
    sys.path.append(str(loader_dir.resolve()))

from api.client import get_backend_dataloader
from features.enhancer import FeatureEnhancer

def prepare_dataloader_from_docker(dataset_id: int, 
                                   backend_url: str = "http://localhost:5000",
                                   batch_size: int = 16,
                                   num_frames: int = 30) -> torch.utils.data.DataLoader:
    """
    Pobiera i rozpakowuje dane z kontenerów Docker, a następnie zwraca PyTorch DataLoader
    z wbudowanym FeatureEnhancer (normalizacja dłoni, odległości geometryczne, prędkości).
    
    Args:
        dataset_id: ID zbioru danych w bazie PostgreSQL do wyeksportowania i pobrania.
        backend_url: Adres URL pod którym dostępny jest backend API (z Windowsa: http://localhost:5000).
        batch_size: Rozmiar paczki danych (batch).
        num_frames: Docelowa liczba klatek (dopełnienie/przycięcie sekwencji landmarków).
        
    Returns:
        torch.utils.data.DataLoader gotowy do pętli uczącej.
    """
    print(f"--- Przygotowywanie DataLoadera dla dataset_id={dataset_id} ---")
    
    # 2. Definiujemy transformacje (Feature Engineering)
    # Wybieramy kluczowe punkty (z 1629 do 116 koordynatów na klatkę), normalizujemy dłonie,
    # obliczamy odległości i prędkości (końcowy kształt klatki to 352 cechy).
    enhancer = FeatureEnhancer(
        use_relative_hands=True,
        use_distances=True,
        use_velocities=True,
        select_keypoints=True
    )
    
    # Katalog na Windowsie, gdzie zostaną zapisane pobrane pliki .npy
    dest_dir = loader_dir / "data" / f"dataset_{dataset_id}"
    
    # 3. Wywołanie klienta API, który zintegruje się z Dockerem
    dataloader = get_backend_dataloader(
        dataset_id=dataset_id,
        backend_url=backend_url,
        dest_dir=dest_dir,
        batch_size=batch_size,
        shuffle=True,
        num_frames=num_frames,
        transform=enhancer,
        num_workers=0  # 0 dla Windowsa, aby uniknąć problemów z wielowątkowością przy debugowaniu
    )
    
    return dataloader

if __name__ == "__main__":
    # Przykład użycia:
    # Upewnij się, że kontenery Docker działają (docker-compose up -d)
    
    dataset_id = 999  # Zmień na właściwe ID zbioru danych
    
    try:
        dataloader = prepare_dataloader_from_docker(
            dataset_id=dataset_id,
            backend_url="http://localhost:5000",
            batch_size=4,
            num_frames=30
        )
        
        print("\nPomyślnie utworzono DataLoader.")
        
        # Testowe przejście przez jedną paczkę
        for batch_idx, (landmarks, labels) in enumerate(dataloader):
            print(f"\n[Test] Batch {batch_idx + 1}:")
            print(f" - Kszałt landmarków (tensor): {landmarks.shape} (Oczekiwano: [batch_size, num_frames, 352])")
            print(f" - Kształt etykiet (tensor):   {labels.shape} (Etykiety klas gestów)")
            print(f" - Wartości etykiet w paczce:   {labels.tolist()}")
            break  # Przerywamy po pierwszym batchu na potrzeby testu
            
    except Exception as e:
        print(f"\n[BŁĄD] Nie udało się pobrać danych lub utworzyć DataLoadera: {e}")
        print("Upewnij się, że:")
        print("1. Kontenery Docker działają (docker-compose ps)")
        print("2. Istnieją dane testowe w bazie (np. po uruchomieniu testu integracyjnego)")
