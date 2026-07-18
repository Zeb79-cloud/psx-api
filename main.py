from fastapi import FastAPI, HTTPException
import yfinance as yf

app = FastAPI()

@app.get("/price")
def get_price(symbol: str):
    try:
        # Yahoo Finance uses .KA for the Karachi Stock Exchange 
        # So "OGDC" becomes "OGDC.KA"
        psx_symbol = f"{symbol.upper()}.KA"
        
        # Fetch the stock data
        stock = yf.Ticker(psx_symbol)
        todays_data = stock.history(period="1d")
        
        if todays_data.empty:
            raise ValueError(f"No trading data found for {symbol}")
            
        # Get the most recent closing/live price
        current_price = todays_data['Close'].iloc[-1]

        # Return the clean data
        return {"symbol": symbol.upper(), "price": round(current_price, 2)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not fetch price. Error: {str(e)}")
