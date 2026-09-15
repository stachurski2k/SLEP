
## Wariant 1: Uruchomienie w kontenerach Docker (Backend + Baza)

### /language-learning-backend
* **Komenda:**
  ```powershell
  docker compose up --build -d
  ```
* **Co robi ta komenda:**
  1. Buduje obraz Dockera dla backendu na podstawie pliku `Dockerfile`.
  2. Pobiera oficjalny obraz PostgreSQL 17 (`postgres:17`).
  3. Uruchamia kontener bazy danych (`language-learning-db`) na porcie `5435` (mapowany z wewnętrznego `5432`).
  4. Czeka na gotowość bazy danych (`healthcheck`).
  5. Uruchamia kontener backendu (`language-learning-api`) na porcie `8000`.
  6. Flaga `-d` uruchamia wszystko w tle (nie blokuje konsoli).

---

## Wariant 2: Uruchomienie lokalne przez Python (do developmentu)

### Krok 1: Uruchomienie samej bazy danych PostgreSQL

Backend potrzebuje działającej bazy danych. Najwygodniej uruchomić ją w Dockerze.

* **Gdzie wpisać:** W katalogu `src/language-learning-backend`.
* **Komenda:**
  ```powershell
  docker compose up postgres -d
  ```
* **Co robi:** Uruchamia wyłącznie kontener z bazą danych PostgreSQL na porcie `5435` w tle.

---

### Krok 2: Przygotowanie środowiska Python i instalacja bibliotek

* **Gdzie wpisać:** W katalogu `src/language-learning-backend`.

* **Opcja A (zalecana – przy użyciu `uv`):**
  ```powershell
  uv venv
  .\.venv\Scripts\activate
  uv pip install -r requirements.txt
  ```
  * **Co robi:** Tworzy wirtualne środowisko, aktywuje je i instaluje wymagane biblioteki (`FastAPI`, `Uvicorn`, `SQLAlchemy`, `asyncpg`, `Pydantic`, itp.).

* **Opcja B (standardowy Python / pip):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  pip install -r requirements.txt
  ```
  * **Co robi:** Standardowe utworzenie i instalacja zależności przez `pip`.

---

### Krok 3: Uruchomienie serwera backendu

* **Gdzie wpisać:** W katalogu `src/language-learning-backend`.

* **Komenda 1 (bezpośrednio przez uvicorn):**
  ```powershell
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```
* **Komenda 2 (alternatywnie bezpośrednio przez python):**
  ```powershell
  python main.py
  ```
* **Co robi ta komenda:**
  1. Wczytuje zmienne środowiskowe z pliku `.env`.
  2. Łączy się z bazą danych PostgreSQL i automatycznie tworzy tabele (`users`, `user_profiles`, `user_preferences`), jeśli jeszcze nie istnieją.
  3. Rejestruje wszystkie trasy API modułu użytkowników (`/api/v1/users`).
  4. Uruchamia serwer HTTP pod adresem `http://localhost:8000`.
  5. Flaga `--reload` nasłuchuje zmian w kodzie i restartuje serwer natychmiast po zapisaniu pliku.

---

## Jak sprawdzić, czy działa?

Po uruchomieniu backendu otwórz przeglądarkę pod adresami:

| Adres URL | Co wyświetla |
| :--- | :--- |
| **http://localhost:8000/docs** | **Interaktywna dokumentacja Swagger UI** – pozwala testować endpointy użytkowników bezpośrednio w przeglądarce. |
| **http://localhost:8000/redoc** | Alternatywna dokumentacja ReDoc. |
| **http://localhost:8000/health** | Status zdrowia serwera (`{"status": "ok"}`). |
| **http://localhost:8000/api/v1/users** | Endpointy API do zarządzania użytkownikami (POST, GET, PUT, DELETE). |


