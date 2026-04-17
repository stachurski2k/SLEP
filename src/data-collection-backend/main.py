from fastapi import FastAPI
from weather import generate_forecast, WeatherForecast
from typing import List

app = FastAPI(
    title="Backend API",
    description="API for fullstack template",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
def read_root():
    return {"Hello": "from backend-py!"}

@app.get("/weather", response_model=List[WeatherForecast])
def get_weather():
    return generate_forecast()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
