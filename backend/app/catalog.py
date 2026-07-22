from __future__ import annotations


STOCKS = {
    "600519": {"name": "贵州茅台", "exchange": "SH", "sector": "食品饮料"},
    "600036": {"name": "招商银行", "exchange": "SH", "sector": "银行"},
    "601318": {"name": "中国平安", "exchange": "SH", "sector": "非银金融"},
    "000333": {"name": "美的集团", "exchange": "SZ", "sector": "家用电器"},
    "300750": {"name": "宁德时代", "exchange": "SZ", "sector": "电力设备"},
    "000001": {"name": "平安银行", "exchange": "SZ", "sector": "银行"},
}


def get_stock(symbol: str) -> dict[str, str]:
    if symbol not in STOCKS:
        raise KeyError(symbol)
    return {"symbol": symbol, **STOCKS[symbol]}

