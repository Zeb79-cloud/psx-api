from fastapi import FastAPI
import yfinance as yf

app = FastAPI()

@app.get("/price")
def get_price(symbol: str):
    # Try the standard .KA suffix
    psx_symbol = f"{symbol.upper()}.KA"
    ticker = yf.Ticker(psx_symbol)
    
    try:
        # Fetch the last 5 days
        data = ticker.history(period="5d")
        
        # If the data is empty, try a fallback (no suffix)
        if data.empty:
            ticker = yf.Ticker(symbol.upper())
            data = ticker.history(period="5d")
            
        # Check again if we found anything
        if data.empty:
            return {"symbol": symbol.upper(), "price": "N/A", "error": "Symbol not found"}
            
        # Extract the last valid closing price
        current_price = data['Close'].iloc[-1]
        return {"symbol": symbol.upper(), "price": round(float(current_price), 2)}

    except Exception:
        # If any other error occurs, return a clean error instead of 500
        return {"symbol": symbol.upper(), "price": "N/A", "error": "Server error"}
