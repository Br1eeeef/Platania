from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.app.data_sources.catalog import INSTRUMENTS, catalog_service  # noqa: E402
from api.app.data_sources.service import market_data_service  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="低频刷新 Platania A股日线缓存")
    parser.add_argument("--symbol", action="append", help="可重复指定，例如 600519.SH")
    parser.add_argument("--demo", action="store_true", help="强制生成确定性演示数据")
    parser.add_argument("--catalog", action="store_true", help="刷新全量 A 股代码目录（每日一次）")
    parser.add_argument("--interval-kind", choices=["1d", "1m", "5m", "15m", "30m", "60m"], default="1d", help="K线周期")
    parser.add_argument("--interval", type=float, default=2.0, help="标的之间的最小等待秒数")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.catalog:
        try:
            logging.info("catalog_refreshed instruments=%s", catalog_service.refresh())
        except Exception as exc:
            logging.error("catalog_refresh_failed error=%s", type(exc).__name__)
            return 1
        if not args.symbol:
            return 0
    symbols = args.symbol or [symbol for symbol, item in INSTRUMENTS.items() if item.status == "active"]
    failed = 0
    for index, symbol in enumerate(symbols):
        try:
            timeframe = args.interval_kind.removesuffix("m") if args.interval_kind.endswith("m") else "1d"
            instrument, frame, meta = market_data_service.refresh(symbol, force_demo=args.demo, timeframe=timeframe)
            logging.info(
                "refreshed symbol=%s rows=%s provider=%s kind=%s", instrument.symbol, len(frame), meta.provider, meta.kind
            )
        except Exception as exc:
            failed += 1
            logging.error("refresh_failed symbol=%s error=%s", symbol, type(exc).__name__)
        if index < len(symbols) - 1:
            time.sleep(max(args.interval, 1.5))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
