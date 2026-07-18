from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Allows your Google Sheet to communicate with the API securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "PSX API is running smoothly!"}

@app.get("/price")
def get_price(symbol: str = Query(..., description="The stock ticker symbol, e.g., OGDC")):
    symbol = symbol.upper().strip()
    url = f"https://dps.psx.com.pk/company/{symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found on PSX.")
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Scrapes the live price from the PSX dashboard page layout
        price_div = soup.find('div', class_='quote__close')
        if not price_div:
            # Fallback layout check if PSX modified their CSS classes
            price_div = soup.find('div', class_='stats_value')
            
        if price_div:
            # Clean up text formatting (removes 'Rs.' or whitespace)
            clean_price = price_div.text.replace("Rs.", "").strip()
            return {"symbol": symbol, "price": clean_price}
        else:
            raise HTTPException(status_code=500, detail="Failed to locate price element on PSX page.")
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error connecting to PSX: {str(e)}")
