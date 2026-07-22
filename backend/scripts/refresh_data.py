from __future__ import annotations

import argparse
import time

from backend.app.catalog import STOCKS
from backend.app.data import MarketDataError
from backend.app.service import repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh Platania local daily-market cache.")
    parser.add_argument("--source", choices=("auto", "akshare", "demo"), default="auto")
    parser.add_argument("--symbol", action="append", choices=tuple(STOCKS), help="Repeat to refresh selected symbols")
    parser.add_argument("--interval", type=float, default=1.5, help="Seconds between provider requests")
    args = parser.parse_args()

    symbols = args.symbol or list(STOCKS)
    failures = 0
    for index, symbol in enumerate(symbols):
        try:
            bars, meta = repository.refresh(symbol, args.source)
            print(f"{symbol}: {len(bars)} bars from {meta['source']}")
        except MarketDataError as exc:
            failures += 1
            print(f"{symbol}: failed - {exc}")
        if index < len(symbols) - 1:
            time.sleep(max(args.interval, 0.5))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

