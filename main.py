from fastapi import FastAPI
import yfinance as yf

app = FastAPI()

@app.get("/price")
def get_price(symbol: str):
    symbol = symbol.upper()
    # Adding the .KA suffix for PSX stocks
    ticker = yf.Ticker(f"{symbol}.KA")
    
    try:
        # Fetch last 2 trading days to compare current price with previous close
        data = ticker.history(period="2d")
        
        # Check if we have enough data (at least 2 days)
        if len(data) < 2:
            return {"symbol": symbol, "price": "N/A", "change_val": "N/A", "change_pct": "N/A"}
            
        current_price = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        
        # Calculate numerical change and percentage change
        change_val = current_price - prev_close
        change_pct = (change_val / prev_close) * 100
        
        return {
            "symbol": symbol, 
            "price": round(float(current_price), 2),
            "change_val": round(float(change_val), 2),
            "change_pct": round(float(change_pct), 2)
        }

    except Exception:
        return {"symbol": symbol, "price": "N/A", "change_val": "N/A", "change_pct": "N/A"}
