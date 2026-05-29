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
            return {"error": "Failed to connect to PSX Portal"}

        html_content = response.text

        # 1. Fetch Current Price (Works perfectly with your existing element)
        price_match = re.search(
            r'<div class="quote__close">([\s\S]*?)</div>', html_content
        )
        current_price = 0.0
        if price_match:
            raw_price = re.sub(r"[^\d.]", "", price_match.group(1))
            current_price = float(raw_price) if raw_price else 0.0

        # 2. Fetch Previous Close (Targeting 'LDCP' class='stats__value')
        ldcp_match = re.search(
            r'LDCP[\s\S]*?class=["\']stats__value["\'][^>]*?>\s*([\d,.]+)',
            html_content,
            re.IGNORECASE,
        )
        prev_close = 0.0
        if ldcp_match:
            prev_close = float(ldcp_match.group(1).replace(",", ""))

        # 3. Fetch 52-Week Range & split the low/high elements safely
        # Matches any non-numeric break (like dashes/spaces) between the values
        range_match = re.search(
            r'52-WEEK RANGE[\s\S]*?class=["\']stats__value["\'][^>]*?>\s*([\d,.]+)\s*[^\d.]+\s*([\d,.]+)',
            html_content,
            re.IGNORECASE,
        )
        low52 = 0.0
        high52 = 0.0
        if range_match:
            low52 = float(range_match.group(1).replace(",", ""))
            high52 = float(range_match.group(2).replace(",", ""))

        # 4. Pure Mathematical Computations (Saves you from parsing volatile HTML spans)
        if prev_close > 0:
            change = current_price - prev_close
            percent_change = (change / prev_close) * 100
        else:
            change = 0.0
            percent_change = 0.0

        return {
            "symbol": symbol.upper(),
            "price": current_price,
            "prev_close": prev_close,
            "change": round(change, 2),
            "percent": round(percent_change, 2),
            "low52": low52,
            "high52": high52,
        }

    except Exception as e:
        return {"error": str(e)}
