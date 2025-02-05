from fastapi import APIRouter, HTTPException, Depends, Query
from enum import Enum
from typing import List, Dict, Optional
from fastapi.security import OAuth2PasswordBearer
import httpx
from pydantic import BaseModel
from app.routers.auth import oauth2_scheme

# Define the router
router = APIRouter(
    prefix="/crypto",
    tags=["crypto"]
)

class SortBy(str, Enum):
    VOLUME = "volume"
    PRICE = "lastPrice"  # Changed from "price" to "lastPrice"
    CHANGE = "priceChangePercent"  # Changed from "change" to "priceChangePercent"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class CryptoTicker(BaseModel):
    symbol: str
    lastPrice: str
    priceChangePercent: str
    volume: str
    highPrice: str
    lowPrice: str
    quoteVolume: str

class CryptoResponse(BaseModel):
    data: List[CryptoTicker]
    count: int
    timestamp: str
    sort_by: str
    sort_order: str

@router.get("/tickers", response_model=CryptoResponse)
async def get_all_tickers(
    token: str = Depends(oauth2_scheme),
    limit: int = Query(10, ge=1, le=100),
    min_volume: float = Query(0, ge=0),
    min_price: float = Query(0, ge=0),
    symbol_filter: Optional[str] = None,
    sort_by: SortBy = Query(SortBy.VOLUME),
    sort_order: SortOrder = Query(SortOrder.DESC),
    min_change: float = Query(-100, ge=-100, le=100),
    max_change: float = Query(100, ge=-100, le=100)
):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://api.binance.com/api/v3/ticker/24hr")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Binance API error: {response.text}")
            
            data = response.json()
            filtered_data = []
            
            for item in data:
                try:
                    price_change = float(item.get("priceChangePercent", 0))
                    volume = float(item.get("volume", 0))
                    price = float(item.get("lastPrice", 0))
                    
                    if (min_volume > 0 and volume < min_volume or
                        min_price > 0 and price < min_price or
                        price_change < min_change or
                        price_change > max_change):
                        continue
                        
                    if symbol_filter and symbol_filter.upper() not in item.get("symbol", "").upper():
                        continue
                        
                    filtered_data.append(CryptoTicker(
                        symbol=item.get("symbol", ""),
                        lastPrice=item.get("lastPrice", "0"),
                        priceChangePercent=item.get("priceChangePercent", "0"),
                        volume=item.get("volume", "0"),
                        highPrice=item.get("highPrice", "0"),
                        lowPrice=item.get("lowPrice", "0"),
                        quoteVolume=item.get("quoteVolume", "0")
                    ))
                except (ValueError, KeyError) as e:
                    print(f"Error processing item: {item}, Error: {str(e)}")
                    continue
            
            # Sort the data
            # Updated sorting logic
            sort_field_map = {
                SortBy.VOLUME: "volume",
                SortBy.PRICE: "lastPrice",
                SortBy.CHANGE: "priceChangePercent"
            }
            sort_field = sort_field_map[sort_by]
            sort_key = lambda x: float(getattr(x, sort_field))
            filtered_data.sort(key=sort_key, reverse=(sort_order == SortOrder.DESC))
            
            # Apply limit
            limited_data = filtered_data[:limit]
            
            return CryptoResponse(
                data=limited_data,
                count=len(limited_data),
                timestamp=str(data[0].get("closeTime", "")) if data else "",
                sort_by=sort_by.value,
                sort_order=sort_order.value
            )
            
    except Exception as e:
        print(f"Error in get_all_tickers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/ticker/{symbol}", response_model=CryptoTicker)
async def get_ticker(symbol: str, token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        return response.json()
from datetime import datetime, timedelta

class CryptoChart(BaseModel):
    timestamps: List[int]
    prices: List[float]

@router.get("/chart/{symbol}")
async def get_crypto_chart(
    symbol: str,
    interval: str = "1h",
    limit: int = 24,
    token: str = Depends(oauth2_scheme)
):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.binance.com/api/v3/klines",
                params={
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "limit": limit
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
            
            data = response.json()
            return CryptoChart(
                timestamps=[entry[0] for entry in data],
                prices=[float(entry[4]) for entry in data]
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))