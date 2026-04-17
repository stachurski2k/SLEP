import random
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

class WeatherForecast(BaseModel):
    date: str
    temperatureC: int
    temperatureF: int
    summary: str

SUMMARIES = [
    "Freezing", "Bracing", "Chilly", "Cool", "Mild", "Warm", "Balmy", "Hot", "Sweltering", "Scorching"
]

def generate_forecast(start_date: datetime = None, days: int = 5) -> List[WeatherForecast]:
    if start_date is None:
        start_date = datetime.now()
    
    forecasts = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        temp_c = random.randint(-20, 55)
        summary = random.choice(SUMMARIES)
        
        forecast = WeatherForecast(
            date=date.strftime("%Y-%m-%d"),
            temperatureC=temp_c,
            temperatureF=32 + int(temp_c / 0.5556),
            summary=summary
        )
        forecasts.append(forecast)
        
    return forecasts
