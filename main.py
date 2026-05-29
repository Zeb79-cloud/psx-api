from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import re

app = FastAPI(title="PSX Live Data Bridge API")

# Enable CORS so Google Sheets can cleanly communicate with your app
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
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Ticker symbol not found on PSX portal")
        elif response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"PSX portal returned HTTP status {response.status_code}")
            
        html_content = response.text
        
        # Scrape structural elements directly out of official CSS classes
        price_match = re.search(r'<div class="quote__close">([\s\S]*?)</div>', html_content)
        change_match = re.search(r'<div class="quote__change">([\s\S]*?)</div>', html_content)
        
        if not price_match:
            raise HTTPException(status_code=404, detail="Unable to extract stock profile page contents")
            
        # Clean price string formatting
        raw_price = price_match.group(1).replace("Rs.", "").replace(",", "").strip()
        price = float(raw_price)
        
        change = 0.0
        percent = 0.0
        
        if change_match:
            # Strip internal sub-tags inside change block if present
            raw_change_text = re.sub(r'<[^>]+>', '', change_match.group(1)).strip()
            
            # Parse typical string output: "-2.50 (-0.45%)"
            if "(" in raw_change_text:
                parts = raw_change_text.split("(")
                change = float(parts[0].replace(",", "").strip())
                raw_percent = parts[1].replace(")", "").replace("%", "").strip()
                percent = float(raw_percent) / 100.0  # Decimals parse cleanly into Google Sheet percentages
                
        return {
            "symbol": clean_symbol,
            "price": price,
            "change": change,
            "percent": percent
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed connecting to upstream host: {str(e)}")
    except ValueError:
        raise HTTPException(status_code=500, detail="Upstream data translation layout parsing error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
