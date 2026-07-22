from __future__ import annotations

from datetime import UTC, datetime, timedelta

from api.app.models.feed import FeedItem, FeedKind, FeedResponse


class FeedService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.demo_items = [
            FeedItem(
                id="demo-signal-1",
                kind=FeedKind.SIGNAL,
                author_name="Platania 策略台",
                title="趋势动量研究池更新",
                excerpt="研究池中 2 个标的满足多周期趋势过滤。信号仅供研究，不构成交易建议。",
                symbol="600036.SH",
                strategy_id="trend_momentum",
                created_at=now - timedelta(minutes=18),
                likes=12,
                comments=3,
                is_demo=True,
            ),
            FeedItem(
                id="demo-research-1",
                kind=FeedKind.RESEARCH,
                author_name="量化笔记",
                title="为什么回测必须使用下一根 K 线成交",
                excerpt="收盘后才能确定的指标不能用同一根 K 线的收盘价成交，否则会引入未来函数。",
                created_at=now - timedelta(hours=3),
                likes=36,
                comments=8,
                is_demo=True,
            ),
            FeedItem(
                id="demo-backtest-1",
                kind=FeedKind.BACKTEST,
                author_name="Demo 研究员",
                title="放量突破策略参数复盘",
                excerpt="在固定种子演示行情上比较 20 日与 55 日突破窗口，并记录交易成本敏感性。",
                symbol="300750.SZ",
                strategy_id="volume_breakout",
                created_at=now - timedelta(days=1),
                likes=21,
                comments=5,
                is_demo=True,
            ),
            FeedItem(
                id="demo-update-1",
                kind=FeedKind.STRATEGY_UPDATE,
                author_name="Platania",
                title="均值回归策略更新至 v1.1",
                excerpt="新增最大持仓天数和沪深 300 长期趋势过滤。",
                strategy_id="mean_reversion",
                created_at=now - timedelta(days=2),
                likes=18,
                comments=2,
                is_demo=True,
            ),
        ]

    def list(self, page: int, page_size: int) -> FeedResponse:
        start = (page - 1) * page_size
        return FeedResponse(
            items=self.demo_items[start : start + page_size],
            page=page,
            page_size=page_size,
            total=len(self.demo_items),
            is_demo=True,
        )


feed_service = FeedService()
