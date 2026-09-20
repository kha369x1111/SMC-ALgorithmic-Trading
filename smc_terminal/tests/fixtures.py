"""
SMC Algorithmic Trading Terminal - Deterministic Test Data Generator.
Produces mathematical, reproducible OHLCV series for unit test verification.
"""

from src.data.models import Candle


def create_candle(
    index: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float = 1000.0,
    interval_ms: int = 300000,  # 5 minutes
) -> Candle:
    base_ts = 1700000000000
    return Candle(
        timestamp=base_ts + index * interval_ms,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        is_closed=True,
    )


def create_candle_series(
    n: int,
    base_price: float = 3000.0,
    trend: str = "FLAT",
    step: float = 1.0,
    interval_ms: int = 300000,
) -> list[Candle]:
    """Generates an n-bar sequence with specified trend."""
    candles = []
    price = base_price
    for i in range(n):
        if trend == "UP":
            price += step
            o = price - step * 0.4
            c = price
            h = price + step * 0.3
            l = o - step * 0.3
        elif trend == "DOWN":
            price -= step
            o = price + step * 0.4
            c = price
            h = o + step * 0.3
            l = price - step * 0.3
        else:
            o = price
            c = price + (step if i % 2 == 0 else -step) * 0.2
            h = max(o, c) + step * 0.5
            l = min(o, c) - step * 0.5

        candles.append(create_candle(i, o, h, l, c, interval_ms=interval_ms))
    return candles


def generate_wave_series(
    base_price: float = 3000.0,
    trend: str = "BULLISH",
    waves: int = 3,
    wave_size: float = 20.0,
    pullback_ratio: float = 0.4,
    interval_ms: int = 300000,
) -> list[Candle]:
    """
    Generates genuine zig-zag waves creating distinct fractal swing highs and lows.
    For BULLISH: HHs and HLs.
    For BEARISH: LHs and LLs.
    """
    candles = []
    price = base_price
    idx = 0

    for w in range(waves):
        # 1. Expansion leg (4 bars)
        exp_step = wave_size / 4.0
        for _ in range(4):
            if trend == "BULLISH":
                o = price
                c = price + exp_step * 0.9
                h = c + exp_step * 0.2
                l = o - exp_step * 0.1
                price = c
            else:
                o = price
                c = price - exp_step * 0.9
                h = o + exp_step * 0.1
                l = c - exp_step * 0.2
                price = c
            candles.append(create_candle(idx, o, h, l, c, interval_ms=interval_ms))
            idx += 1

        # 2. Retracement leg (4 bars)
        pb_size = wave_size * pullback_ratio
        pb_step = pb_size / 4.0
        for _ in range(4):
            if trend == "BULLISH":
                o = price
                c = price - pb_step * 0.9
                h = o + pb_step * 0.1
                l = c - pb_step * 0.2
                price = c
            else:
                o = price
                c = price + pb_step * 0.9
                h = c + pb_step * 0.2
                l = o - pb_step * 0.1
                price = c
            candles.append(create_candle(idx, o, h, l, c, interval_ms=interval_ms))
            idx += 1

    return candles


def generate_fractal_high_series() -> list[Candle]:
    """
    Produces a 7-bar sequence with a clear 3-bar fractal swing high at index 3:
    Bar 0: [100, 105, 98, 102]
    Bar 1: [102, 110, 101, 108]
    Bar 2: [108, 115, 106, 112]
    Bar 3: [112, 125, 111, 120] -> Peak high = 125
    Bar 4: [120, 122, 115, 118]
    Bar 5: [118, 119, 112, 114]
    Bar 6: [114, 115, 108, 110]
    Confirmed at index 3 + 3 = 6.
    """
    data = [
        (100.0, 105.0, 98.0, 102.0),
        (102.0, 110.0, 101.0, 108.0),
        (108.0, 115.0, 106.0, 112.0),
        (112.0, 125.0, 111.0, 120.0),  # Pivot High (125.0)
        (120.0, 122.0, 115.0, 118.0),
        (118.0, 119.0, 112.0, 114.0),
        (114.0, 115.0, 108.0, 110.0),
    ]
    return [create_candle(i, o, h, l, c) for i, (o, h, l, c) in enumerate(data)]


def generate_bullish_fvg_series() -> list[Candle]:
    """
    Produces a 3-bar sequence forming a Bullish FVG:
    Bar 0: High = 100
    Bar 1: Aggressive displacement up [101 -> 120], Low=101, High=121
    Bar 2: Low = 108 (which is > Bar 0 High of 100) -> Gap from 100 to 108!
    """
    return [
        create_candle(0, 95.0, 100.0, 94.0, 99.0),
        create_candle(1, 101.0, 121.0, 101.0, 120.0),
        create_candle(2, 120.0, 125.0, 108.0, 124.0),
        create_candle(3, 124.0, 126.0, 104.0, 115.0), # Bar 3 dips to 104 -> Mitigates 50% CE (104)
    ]


def generate_bearish_fvg_series() -> list[Candle]:
    """
    Produces a 3-bar sequence forming a Bearish FVG:
    Bar 0: Low = 120
    Bar 1: Aggressive displacement down [118 -> 100], High=118, Low=99
    Bar 2: High = 112 (which is < Bar 0 Low of 120) -> Gap from 112 to 120!
    """
    return [
        create_candle(0, 125.0, 128.0, 120.0, 122.0),
        create_candle(1, 118.0, 118.0, 99.0, 100.0),
        create_candle(2, 100.0, 112.0, 98.0, 102.0),
    ]


def generate_equal_highs_and_sweep_series() -> list[Candle]:
    """
    Creates two swing highs at almost identical price (~150.0),
    followed by a piercing bar to 151.0 that closes back down at 148.0 (Sweep & Reclaim).
    """
    candles: list[Candle] = []
    # Build first swing high at 150.0
    candles.append(create_candle(0, 140, 142, 139, 141))
    candles.append(create_candle(1, 141, 146, 140, 145))
    candles.append(create_candle(2, 145, 148, 144, 147))
    candles.append(create_candle(3, 147, 150.0, 146, 149)) # High 1 = 150.0
    candles.append(create_candle(4, 149, 149.5, 145, 146))
    candles.append(create_candle(5, 146, 147, 142, 143))
    candles.append(create_candle(6, 143, 144, 140, 142))
    # Pullback and build second swing high at 150.05 (Equal High EQH)
    candles.append(create_candle(7, 142, 146, 141, 145))
    candles.append(create_candle(8, 145, 148, 144, 147))
    candles.append(create_candle(9, 147, 150.05, 146, 149)) # High 2 = 150.05 (~0.03% diff)
    candles.append(create_candle(10, 149, 149.2, 144, 145))
    candles.append(create_candle(11, 145, 146, 141, 142))
    candles.append(create_candle(12, 142, 143, 139, 141))
    # Liquidity Sweep bar: pierces to 151.20, then slams down to close at 147.50 (Reclaim)
    candles.append(create_candle(13, 141, 151.20, 140, 147.50))
    return candles


def generate_equal_lows_and_sweep_series() -> list[Candle]:
    """
    Creates two swing lows at almost identical price (~100.0),
    followed by a piercing bar down to 98.80 that closes back up at 103.0 (Sweep & Reclaim).
    """
    candles: list[Candle] = []
    # Build first swing low at 100.0
    candles.append(create_candle(0, 110, 112, 108, 109))
    candles.append(create_candle(1, 109, 110, 104, 105))
    candles.append(create_candle(2, 105, 106, 101, 102))
    candles.append(create_candle(3, 102, 104, 100.0, 103))  # Low 1 = 100.0
    candles.append(create_candle(4, 103, 106, 102, 105))
    candles.append(create_candle(5, 105, 108, 104, 107))
    candles.append(create_candle(6, 107, 109, 105, 108))
    # Pullback down and build second swing low at 99.95 (Equal Low EQL)
    candles.append(create_candle(7, 108, 108, 104, 105))
    candles.append(create_candle(8, 105, 106, 102, 103))
    candles.append(create_candle(9, 103, 104, 99.95, 103))  # Low 2 = 99.95 (~0.05% diff)
    candles.append(create_candle(10, 103, 106, 102, 105))
    candles.append(create_candle(11, 105, 108, 104, 107))
    candles.append(create_candle(12, 107, 109, 105, 108))
    # Liquidity Sweep bar: pierces down to 98.80, then rockets up to close at 103.50 (Reclaim)
    candles.append(create_candle(13, 108, 109, 98.80, 103.50))
    return candles

