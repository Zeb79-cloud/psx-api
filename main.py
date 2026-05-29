from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import re

app = FastAPI(title="PSX Live Data Bridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/psx")
def get_psx_ticker(symbol: str):
    if not symbol:
        raise HTTPException(status_code=400, detail="Missing stock symbol parameter")
        
    clean_symbol = symbol.upper().strip()
    url = f"https://dps.psx.com.pk/company/{clean_symbol}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="PSX portal unreachable")
            
        html_content = response.text
        
        # 1. Extract live close price
        price_match = re.search(r'<div class="quote__close">([\s\S]*?)</div>', html_content)
        if not price_match:
            raise HTTPException(status_code=404, detail="Ticker symbol not found")
            
        price = float(price_match.group(1).replace("Rs.", "").replace(",", "").strip())
        
        # 2. Extract Static Previous Close (Tag-agnostic extraction regex pattern)
        prev_close = 0.0
        prev_match = re.search(r'Prev\. Close[\s\S]*?class="stats__value">([\s\S]*?)</', html_content)
        if prev_match:
            prev_close = float(prev_match.group(1).replace(",", "").strip())

        # 3. Mathematical data processing logic
        change = 0.0
        percent = 0.0
        if prev_close > 0:
            change = round(price - prev_close, 2)
            percent = round(change / prev_close, 4)
                
        # 4. Extract 52-Week High and Low boundaries
        high_52w = 0.0
        low_52w = 0.0
        
        high_match = re.search(r'52 Week High[\s\S]*?class="stats__value">([\s\S]*?)</', html_content)
        low_match = re.search(r'52 Week Low[\s\S]*?class="stats__value">([\s\S]*?)</', html_content)
        
        if high_match:
            high_52w = float(high_match.group(1).replace(",", "").strip())
        if low_match:
            low_52w = float(low_match.group(1).replace(",", "").strip())
            
        return {
            "symbol": clean_symbol,
            "price": price,
            "change": change,
            "percent": percent,
            "high52": high_52w,
            "low52": low_52w
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
