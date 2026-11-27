# Language Learning Backend

Moduł backendowy aplikacji do nauki języka migowego (SLEP).

## Szybki start

Szczegółową instrukcję uruchomienia krok po kroku znajdziesz w pliku:
👉 **[URUCHOMIENIE.md](./URUCHOMIENIE.md)**

### Uruchomienie w 1 komendzie (Docker):
```bash
docker compose up --build -d
```
API dostępne pod: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

### Uruchomienie lokalne (Python):
```bash
docker compose up postgres -d
pip install -r requirements.txt
python main.py
```

## Struktura projektu

- `main.py` – wejście aplikacji FastAPI, łączenie tras i cykl życia (lifespan)
- `shared/` – konfiguracja połączenia z bazą danych PostgreSQL (SQLAlchemy async)
- `modules/users/` – moduł użytkowników z architekturą warstwową (domain, application, infrastructure, presentation)
- `Dockerfile` & `docker-compose.yml` – konfiguracja środowiska kontenerowego
- `.env` – zmienne konfiguracyjne
