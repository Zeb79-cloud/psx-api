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
        
        # 1. Extract Live Current Price
        price_match = re.search(r'<div class="quote__close">([\s\S]*?)</div>', html_content)
        if not price_match:
            raise HTTPException(status_code=404, detail="Ticker symbol not found")
            
        price = float(price_match.group(1).replace("Rs.", "").replace(",", "").strip())
        
        # 2. Extract Static LDCP (Previous Close) using broad cell matching
        prev_close = 0.0
        prev_match = re.search(r'LDCP[\s\S]*?<div[^>]*?>\s*([\d,.]+)\s*</div>', html_content, re.IGNORECASE)
        if prev_match:
            prev_close = float(prev_match.group(1).replace(",", "").strip())

        # 3. Calculate Bulletproof Intraday Change Metrics inside Python
        change = 0.0
        percent = 0.0
        if prev_close > 0:
            change = round(price - prev_close, 2)
            percent = round((change / prev_close), 4) # Returns decimal for Google Sheets % formatting
                
        # 4. Extract 52-Week Range using character-set agnostic extraction
        high_52w = 0.0
        low_52w = 0.0
        range_match = re.search(r'52-WEEK RANGE[\s\S]*?<div[^>]*?>\s*([\d,.]+)\s*[^0-9.,]+\s*([\d,.]+)\s*</div>', html_content, re.IGNORECASE)
        
        if range_match:
            low_52w = float(range_match.group(1).replace(",", "").strip())
            high_52w = float(range_match.group(2).replace(",", "").strip())
            
        # 5. Calculate 1-Year Performance Change Percentage based on 52-Week Floor
        year_change_percent = 0.0
        if low_52w > 0:
            year_change_percent = round(((price - low_52w) / low_52w), 4)
            
        return {
            "symbol": clean_symbol,
            "price": price,
            "change": change,
            "percent": percent,
            "prev_close": prev_close,
            "high52": high_52w,
            "low52": low_52w,
            "year_change_percent": year_change_percent
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
