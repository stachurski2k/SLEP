FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Instalacja zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu źródłowego
COPY . /app

EXPOSE 8000

# Domyślna komenda uruchamiająca serwer API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
