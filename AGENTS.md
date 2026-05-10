# SLEP

Projekt do tłumaczenia języka migowego oraz zbierania i opisywania danych wideo.
Środowisko robocze: Windows 11, PowerShell.

## Stack
- Frontend: React 19, TypeScript, Vite, React Router, Tailwind CSS, ESLint.
- Backend: Python 3.12, FastAPI, Pydantic, SQLAlchemy async, Alembic, PostgreSQL, Redis, Celery, MinIO/S3, MediaPipe.
- Infrastruktura lokalna: Docker Compose, `uv` dla backendu, `npm.cmd` dla frontendu na PowerShellu.

## Najważniejsze ścieżki
- Frontend: `src/data-collection-frontend`
- Główna aplikacja frontendu: `src/data-collection-frontend/src/App.tsx`
- Routing frontendu: `src/data-collection-frontend/src/routes.ts`
- Backend: `src/data-collection-backend`
- API FastAPI: `src/data-collection-backend/app/main.py`
- Routery backendu: `src/data-collection-backend/app/api/v1`
- Konfiguracja backendu: `src/data-collection-backend/app/core/config.py`
- Docker Compose: `docker-compose.yml`

## Komendy
- Uruchomienie środowiska dev: `docker compose up s3-dev data-collection-api data-collection-worker data-collection-flower postgres redis -d`
- Zatrzymanie środowiska: `docker compose down`
- Frontend lint: `cd src/data-collection-frontend; npm.cmd run lint`
- Frontend build: `cd src/data-collection-frontend; npm.cmd run build`
- Backend testy: `cd src/data-collection-backend; uv run pytest`
- Backend migracje: `cd src/data-collection-backend; uv run alembic upgrade head`

## Zasady dla agenta
- Nie zostawiaj uruchomionych dev serverów ani kontenerów po pracy, chyba że użytkownik wyraźnie o to prosi.
- Nie cofaj cudzych zmian w working tree. Jeśli są niezwiązane z zadaniem, ignoruj je.
- Zbieraj tylko kontekst potrzebny do zadania i trzymaj zmiany blisko dotkniętego obszaru.
- Upraszczaj kod, unikaj zbędnych abstrakcji, preferuj istniejące wzorce projektu.
- Możesz dodać bibliotekę, jeśli realnie upraszcza rozwiązanie albo ogranicza ryzyko błędów.
- Przy zmianach frontendu uruchom `npm.cmd run lint` i `npm.cmd run build`, jeśli jest to wykonalne.
- Przy zmianach backendu uruchom adekwatne testy przez `uv run pytest`; przy modelach bazy sprawdź migracje Alembic.

## Konwencje
- Frontend ma spójny ciemny motyw i użytkowy, profesjonalny charakter.
- Style frontendu pisz w Tailwind CSS. `src/index.css` zostaw jako globalne wejście Tailwinda i bazowe style dokumentu.
- Wspólne klasy UI trzymaj w `src/data-collection-frontend/src/ui/classes.ts`, jeśli powtarzają się w kilku komponentach.
- Nawigację frontendu opieraj o React Router; definicje ścieżek trzymaj w `src/data-collection-frontend/src/routes.ts`.
- Typy i funkcje API frontendu trzymaj w `src/data-collection-frontend/src/actions.ts`, dopóki projekt nie potrzebuje osobnej warstwy klienta API.
- W backendzie dodawaj endpointy w `app/api/v1/<obszar>/router.py`, CRUD w `app/crud`, logikę integracyjną w `app/services`.
- Modele SQLAlchemy, schematy Pydantic i migracje Alembic aktualizuj razem.
- Długie operacje przetwarzania wideo przenoś do Celery zamiast blokować request HTTP.
