from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from typing import List, Dict
from pydantic import BaseModel

class Location(BaseModel):
    latitude: float
    longitude: float

class Station(BaseModel):
    id: str
    device_id: str
    name: str
    location: Location

class WeatherReading(BaseModel):
    station_id: str
    value: float

class WeatherData(BaseModel):
    timestamp: str
    readings: List[WeatherReading]

router = APIRouter(
    prefix="/weather",
    tags=["weather"]
)

@router.get("/stations", response_model=List[Station])
async def get_stations():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.data.gov.sg/v1/environment/air-temperature")
        data = response.json()
        return data["metadata"]["stations"]

@router.get("/current", response_model=WeatherData)
async def get_current_weather():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.data.gov.sg/v1/environment/air-temperature")
        data = response.json()
        return data["items"][0]

@router.get("/station/{station_id}")
async def get_station_weather(station_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.data.gov.sg/v1/environment/air-temperature")
        data = response.json()
        
        # Find the station data
        station = next((s for s in data["metadata"]["stations"] if s["id"] == station_id), None)
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
            
        # Find the current reading for this station
        reading = next((r for r in data["items"][0]["readings"] if r["station_id"] == station_id), None)
        
        return {
            "station": station,
            "current_reading": reading,
            "timestamp": data["items"][0]["timestamp"]
        }
from fastapi import APIRouter, HTTPException
import httpx
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.routers.auth import oauth2_scheme

router = APIRouter(
    prefix="/weather",
    tags=["weather"]
)

class WeatherStation(BaseModel):
    station_id: str
    station_name: str
    location: dict
    temperature: float

class WeatherResponse(BaseModel):
    stations: List[WeatherStation]
    timestamp: str

@router.get("/temperature", response_model=WeatherResponse)
async def get_temperature(token: str = Depends(oauth2_scheme)):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://api.data.gov.sg/v1/environment/air-temperature")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch weather data")
            
            data = response.json()
            stations = []
            
            for reading in data["items"][0]["readings"]:
                station_metadata = next(
                    (station for station in data["metadata"]["stations"] 
                     if station["id"] == reading["station_id"]),
                    None
                )
                
                if station_metadata:
                    stations.append(WeatherStation(
                        station_id=reading["station_id"],
                        station_name=station_metadata["name"],
                        location=station_metadata["location"],
                        temperature=reading["value"]
                    ))
            
            return WeatherResponse(
                stations=stations,
                timestamp=data["items"][0]["timestamp"]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))