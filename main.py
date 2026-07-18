from fastapi import FastAPI, HTTPException
import yfinance as yf

app = FastAPI()

@app.get("/price")
def get_price(symbol: str):
    try:
        # Yahoo Finance uses .KA for the Karachi Stock Exchange 
        psx_symbol = f"{symbol.upper()}.KA"
        
        # Fetch the last 5 days of data to account for weekends and holidays
        stock = yf.Ticker(psx_symbol)
        recent_data = stock.history(period="5d")
        
        if recent_data.empty:
            raise ValueError(f"No trading data found for {symbol}")
            
        # Get the very last available closing price from the dataset
        current_price = recent_data['Close'].iloc[-1]

        # Return the clean data
        return {"symbol": symbol.upper(), "price": round(current_price, 2)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch price. Error: {str(e)}")
