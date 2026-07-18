from fastapi import FastAPI
import yfinance as yf

app = FastAPI()

@app.get("/price")
def get_price(symbol: str):
    symbol = symbol.upper()
    # Try Yahoo Finance
    ticker = yf.Ticker(f"{symbol}.KA")
    
    try:
        # Fetching data with a longer period to ensure we get *something*
        data = ticker.history(period="5d")
        
        # If Yahoo returns data, return it
        if not data.empty:
            return {"symbol": symbol, "price": round(float(data['Close'].iloc[-1]), 2)}
        
        # If Yahoo fails, return a specific message
        return {"symbol": symbol, "price": "Not Found on YF"}

    except Exception:
        return {"symbol": symbol, "price": "Error"}
