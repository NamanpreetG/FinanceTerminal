import requests
import pandas as pd

API_KEY  = "1HE5CQRE0I41XB1V"
BASE_URL = "https://www.alphavantage.co/query"


class FinanceDataFetcher:
    def __init__(self, api_key: str = API_KEY):
        self.api_key  = api_key
        self.base_url = BASE_URL

    # ── Internal helper ───────────────────────────────────────────────────────

    def _get(self, params: dict) -> dict:
        params = {**params, "apikey": self.api_key}
        resp = requests.get(self.base_url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "Information" in data or "Note" in data:
            msg = data.get("Information") or data.get("Note")
            raise RuntimeError(f"API rate limit: {msg}")
        return data

    # ── Public API methods ────────────────────────────────────────────────────

    def global_quote(self, ticker: str) -> dict:
        """Return dict with price, change, volume, etc. for *ticker*."""
        data = self._get({"function": "GLOBAL_QUOTE", "symbol": ticker})
        return data.get("Global Quote", {})

    def daily_series(self, ticker: str) -> pd.DataFrame:
        """Return DataFrame (Date, Open, High, Low, Close, Volume) sorted ascending."""
        data = self._get({
            "function":   "TIME_SERIES_DAILY",
            "symbol":     ticker,
            "outputsize": "compact",
        })
        series = data.get("Time Series (Daily)", {})
        if not series:
            return pd.DataFrame()

        df = pd.DataFrame(series).T
        df.index.name = "Date"
        df.reset_index(inplace=True)
        df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]

        for col in ("Open", "High", "Low", "Close", "Volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values("Date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def overview(self, ticker: str) -> dict:
        """Return dict with company fundamentals (name, sector, P/E, etc.)."""
        return self._get({"function": "OVERVIEW", "symbol": ticker})

    def news(self, ticker: str = "", limit: int = 20) -> list:
        """Return list of article dicts.
        Passes *ticker* to NEWS_SENTIMENT when provided; falls back to
        topics=financial_markets for general market headlines.
        """
        params: dict = {"function": "NEWS_SENTIMENT", "limit": limit}
        if ticker:
            params["tickers"] = ticker
        else:
            params["topics"] = "financial_markets"
        data = self._get(params)
        return data.get("feed", [])
