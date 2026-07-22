from __future__ import annotations

from api.app.models.market import Instrument

INSTRUMENTS: dict[str, Instrument] = {
    "600519.SH": Instrument(symbol="600519.SH", code="600519", name="贵州茅台", exchange="SH", sector="食品饮料"),
    "600036.SH": Instrument(symbol="600036.SH", code="600036", name="招商银行", exchange="SH", sector="银行"),
    "601318.SH": Instrument(symbol="601318.SH", code="601318", name="中国平安", exchange="SH", sector="非银金融"),
    "000333.SZ": Instrument(symbol="000333.SZ", code="000333", name="美的集团", exchange="SZ", sector="家用电器"),
    "300750.SZ": Instrument(symbol="300750.SZ", code="300750", name="宁德时代", exchange="SZ", sector="电力设备"),
    "000001.SZ": Instrument(symbol="000001.SZ", code="000001", name="平安银行", exchange="SZ", sector="银行"),
    "000300.SH": Instrument(symbol="000300.SH", code="000300", name="沪深300", exchange="SH", sector="宽基指数"),
}


def normalize_symbol(value: str) -> str:
    cleaned = value.strip().upper().replace(" ", "")
    if cleaned in INSTRUMENTS:
        return cleaned
    if cleaned.startswith(("SH", "SZ")) and len(cleaned) == 8:
        cleaned = f"{cleaned[2:]}.{cleaned[:2]}"
    if cleaned.isdigit() and len(cleaned) == 6:
        exchange = "SH" if cleaned.startswith(("5", "6", "9")) else "SZ"
        cleaned = f"{cleaned}.{exchange}"
    if cleaned not in INSTRUMENTS:
        raise ValueError(f"unsupported A-share symbol: {value}")
    return cleaned


def get_instrument(value: str) -> Instrument:
    return INSTRUMENTS[normalize_symbol(value)]
