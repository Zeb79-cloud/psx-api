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
        raise HTTPException(status_code=400, detail="Missing stock symbol")
        
    clean_symbol = symbol.upper().strip()
    url = f"https://dps.psx.com.pk/company/{clean_symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text
        
        # 1. Price
        p_match = re.search(r'quote__close">([\d,.]+)', html)
        price = float(p_match.group(1).replace(",", "")) if p_match else 0.0
        
        # 2. LDCP (Prev Close)
        pc_match = re.search(r'LDCP[\s\S]*?stats__value[^>]*?>\s*([\d,.]+)', html, re.IGNORECASE)
        prev_close = float(pc_match.group(1).replace(",", "")) if pc_match else 0.0
        
        # 3. 52-Week Low (More flexible regex)
        low_match = re.search(r'52-WEEK RANGE[\s\S]*?stats__value[^>]*?>\s*([\d,.]+)', html, re.IGNORECASE)
        low_52 = float(low_match.group(1).replace(",", "")) if low_match else prev_close
        
        # 4. Math
        change = price - prev_close
        percent = (change / prev_close) if prev_close > 0 else 0.0
        # 1-Year Change: Logic: (Current - Low) / Low
        year_change = ((price - low_52) / low_52) if low_52 > 0 else 0.0
            
        return {
            "price": price,
            "change": round(change, 2),
            "percent": round(percent, 4),
            "prev_close": prev_close,
            "low52": low_52,
            "year_change_percent": round(year_change, 4)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
