"""Fetch recent Taiwan stock prices from FinLab and write site/data/prices.json."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from finlab import data

LOOKBACK_DAYS = 250  # about one trading year; the page matches windows inside this range
MIN_DAYS = 20  # stocks with fewer valid closes are dropped
OUT_PATH = Path(__file__).parent / "site" / "data" / "prices.json"


def round_sig(x: float, digits: int = 5) -> float | None:
    if x is None or not math.isfinite(x):
        return None
    if x == 0:
        return 0.0
    return round(x, digits - 1 - int(math.floor(math.log10(abs(x)))))


def main() -> None:
    # FinLab authenticates on its own: ~/.finlab/credentials.json locally, or
    # FINLAB_REFRESH_TOKEN / FINLAB_SESSION_ID / FINLAB_API_KEY in CI.

    # Adjusted close, so ex-dividend gaps don't distort the shape.
    close = data.get("etl:adj_close").tail(LOOKBACK_DAYS)
    info = data.get("company_basic_info")
    info = info[info["市場別"].isin(["sii", "otc"])].drop_duplicates("stock_id").set_index("stock_id")

    ids = [sid for sid in close.columns if sid in info.index]
    close = close[ids]
    close = close.loc[:, close.notna().sum() >= MIN_DAYS]

    stocks, series = [], []
    for sid in close.columns:
        row = info.loc[sid]
        stocks.append({
            "id": sid,
            "name": str(row["公司簡稱"]),
            "market": "上市" if row["市場別"] == "sii" else "上櫃",
            "industry": str(row["產業類別"]),
        })
        series.append([round_sig(v) for v in close[sid].tolist()])

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dates": [d.strftime("%Y-%m-%d") for d in close.index],
        "stocks": stocks,
        "close": series,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(stocks)} stocks x {len(close.index)} days "
          f"({payload['dates'][0]} ~ {payload['dates'][-1]}) -> {OUT_PATH} "
          f"[{OUT_PATH.stat().st_size / 1e6:.1f} MB]")


if __name__ == "__main__":
    main()
