from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from api.app.core.config import settings
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


class InstrumentCatalog:
    """Local, daily-refreshed A-share universe; never fetches on each symbol lookup."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or settings.cache_dir
        self.path = self.root / "instruments.json"
        self._items: dict[str, Instrument] = dict(INSTRUMENTS)
        self.updated_at: datetime | None = None
        self._load_cached()

    def _load_cached(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            values = [Instrument.model_validate(item) for item in payload.get("items", [])]
            if values:
                self._items = {item.symbol: item for item in values}
                self._items.setdefault("000300.SH", INSTRUMENTS["000300.SH"])
                self.updated_at = datetime.fromisoformat(payload["updated_at"].replace("Z", "+00:00"))
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return

    @property
    def is_stale(self) -> bool:
        return self.updated_at is None or datetime.now(UTC) - self.updated_at.astimezone(UTC) > timedelta(hours=24)

    def list(self, search: str = "") -> list[Instrument]:
        values = [item for item in self._items.values() if item.sector != "宽基指数"]
        if search:
            token = search.strip().lower()
            values = [
                item
                for item in values
                if token in item.symbol.lower()
                or token in item.code
                or token in item.name.lower()
                or token in item.sector.lower()
            ]
        return sorted(values, key=lambda item: item.symbol)

    def refresh(self) -> int:
        from .akshare_provider import AkshareProvider

        values = AkshareProvider().fetch_instruments()
        self.root.mkdir(parents=True, exist_ok=True)
        now = datetime.now(UTC)
        payload = {"updated_at": now.isoformat(), "items": [item.model_dump(mode="json") for item in values]}
        temp = self.path.with_suffix(".tmp.json")
        temp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.path)
        self._items = {item.symbol: item for item in values}
        self._items.setdefault("000300.SH", INSTRUMENTS["000300.SH"])
        self.updated_at = now
        return len(values)

    def get(self, value: str) -> Instrument:
        symbol = normalize_symbol(value)
        if symbol in self._items:
            return self._items[symbol]
        code, exchange = symbol.split(".")
        return Instrument(symbol=symbol, code=code, name=code, exchange=exchange, sector="待同步")


def normalize_symbol(value: str) -> str:
    cleaned = value.strip().upper().replace(" ", "")
    if cleaned.startswith(("SH", "SZ")) and len(cleaned) == 8:
        cleaned = f"{cleaned[2:]}.{cleaned[:2]}"
    if cleaned.isdigit() and len(cleaned) == 6:
        if cleaned.startswith("9"):
            raise ValueError(f"unsupported A-share symbol: {value}")
        exchange = "SH" if cleaned.startswith(("5", "6")) else "SZ"
        cleaned = f"{cleaned}.{exchange}"
    if (
        len(cleaned) != 9
        or cleaned[6] != "."
        or cleaned[:6].isdigit() is False
        or cleaned[7:] not in {"SH", "SZ"}
        or cleaned.startswith("9")
    ):
        raise ValueError(f"unsupported A-share symbol: {value}")
    return cleaned


catalog_service = InstrumentCatalog()


def get_instrument(value: str) -> Instrument:
    return catalog_service.get(value)
