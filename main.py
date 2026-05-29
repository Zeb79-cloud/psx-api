import re
import requests


def fetch_psx_stock_data(symbol: str):
    url = f"https://dps.psx.com.pk/company/{symbol.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"error": f"Failed to connect (Status: {response.status_code})"}

        html = response.text

        # 1. Extract Current Price (Targeting the massive top element)
        price_match = re.search(
            r'<div class="quote__close">([\s\S]*?)</div>', html
        )
        current_price = 0.0
        if price_match:
            # Strip out everything that isn't a digit or a decimal point
            raw_price = re.sub(r"[^\d.]", "", price_match.group(1))
            current_price = float(raw_price) if raw_price else 0.0

        # 2. Extract Previous Close (LDCP value)
        ldcp_match = re.search(
            r"LDCP[\s\S]*?<div class=\"stats__value\">\s*([\d,.]+)",
            html,
            re.IGNORECASE,
        )
        prev_close = 0.0
        if ldcp_match:
            prev_close = float(ldcp_match.group(1).replace(",", ""))

        # 3. Extract 52-Week Range and separate them cleanly
        range_match = re.search(
            r"52-WEEK RANGE[\s\S]*?<div class=\"stats__value\">\s*([\d,.]+)\s*[^\d.]+\s*([\d,.]+)",
            html,
            re.IGNORECASE,
        )
        low_52 = 0.0
        high_52 = 0.0
        if range_match:
            low_52 = float(range_match.group(1).replace(",", ""))
            high_52 = float(range_match.group(2).replace(",", ""))

        # 4. Math Over Scraping: Safely calculate change values locally
        if prev_close > 0:
            change = current_price - prev_close
            percent_change = (change / prev_close) * 100
        else:
            change = 0.0
            percent_change = 0.0

        return {
            "Symbol": symbol.upper(),
            "Current Price": current_price,
            "Prev Close (LDCP)": prev_close,
            "Net Change": round(change, 2),
            "Percent Change (%)": round(percent_change, 2),
            "52W Low": low_52,
            "52W High": high_52,
        }

    except Exception as e:
        return {"error": f"Scraping error: {str(e)}"}


# Test execution
if __name__ == "__main__":
    # Test using Lucky Cement from your screenshot example
    data = fetch_psx_stock_data("LUCK")
    print(data)
