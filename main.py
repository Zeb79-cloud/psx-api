from fastapi import FastAPI, HTTPException, Query
import yfinance as yf

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "usage": "/price?symbol=OGDC"}

@app.get("/price")
def get_price(symbol: str = Query(..., description="PSX ticker, e.g. OGDC")):
    symbol = symbol.strip().upper()
    ticker_symbol = f"{symbol}.KA"

    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="5d")  # 5d buffer in case of holidays/gaps

        if data is None or len(data) < 2:
            return {
                "symbol": symbol,
                "price": "N/A",
                "change_val": "N/A",
                "change_pct": "N/A",
                "note": "Not enough trading history returned from Yahoo Finance"
            }

        current_price = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]

        change_val = current_price - prev_close
        change_pct = (change_val / prev_close) * 100

        return {
            "symbol": symbol,
            "price": round(float(current_price), 2),
            "change_val": round(float(change_val), 2),
            "change_pct": round(float(change_pct), 2)
        }

    except Exception as e:
        # Surface the real error instead of hiding it
        raise HTTPException(status_code=500, detail=f"Error fetching {symbol}: {str(e)}")
