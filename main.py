from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import re

app = FastAPI()

@app.get("/psx")
def get_psx_ticker(symbol: str):
    url = f"https://dps.psx.com.pk/company/{symbol.upper().strip()}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text
        
        # 1. Price
        p_match = re.search(r'quote__close">([\d,.]+)', html)
        price = float(p_match.group(1).replace(",", "")) if p_match else 0.0
        
        # 2. LDCP (Prev Close)
        pc_match = re.search(r'LDCP[\s\S]*?stats__value[^>]*?>\s*([\d,.]+)', html, re.IGNORECASE)
        prev_close = float(pc_match.group(1).replace(",", "")) if pc_match else price
        
        # 3. 52-Week Low (The Logic Fix)
        low_match = re.search(r'52-WEEK RANGE[\s\S]*?stats__value[^>]*?>\s*([\d,.]+)', html, re.IGNORECASE)
        low_52 = float(low_match.group(1).replace(",", "")) if low_match else 0.0
        
        # FALLBACK: If low_52 is 0, use prev_close so math doesn't return 0%
        effective_low = low_52 if low_52 > 0 else prev_close
        
        # 4. Math
        change = price - prev_close
        percent = (change / prev_close) if prev_close > 0 else 0.0
        year_change = ((price - effective_low) / effective_low) if effective_low > 0 else 0.0
            
        return {
            "price": price,
            "change": round(change, 2),
            "percent": round(percent, 4),
            "prev_close": prev_close,
            "year_change_percent": round(year_change, 4)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
