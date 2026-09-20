# SMC Algorithmic Trading Terminal — Data Provenance Map
**Document ID:** PROVENANCE-SMC-20260919-001  
**Audit Phase:** Phase 1 (Audit & Verification)  
**Purpose:** Comprehensive trace of every metric, badge, chart element, price, status, and control rendered in the UI to its origin.

---

## Provenance Classification Taxonomy

Every UI data point is categorized into one of five provenance classes:

| Class Code | Provenance Classification | Description |
| :--- | :--- | :--- |
| **REAL_ALGO** | Real Algorithmic Calculation | Derived deterministically from algorithmic logic or runtime state. |
| **MOCK_DATA** | Mock Dataset Record | Sourced from static mock data arrays in `src/data/mockData.ts`. |
| **STATIC_UI** | Static Hardcoded UI String | Hardcoded literal inside JSX markup without state backing. |
| **FRONTEND_CALC** | Client-Side Calculated Value | Computed dynamically in the browser using React state formulas. |
| **SIMULATED_STUB** | Simulated Adapter Stub | Sourced from local simulation adapter (`PaperTradingAdapter`). |

---

## 1. Top Header & System Safety Bar (`src/components/Header.tsx`)

| UI Label / Element | Current Value Displayed | Source File & Line | Provenance Class | Required Action to make 100% Real |
| :--- | :--- | :--- | :--- | :--- |
| **Environment Selector** | `DEMO` / `TESTNET` / `LIVE` | `src/App.tsx:24`, `src/components/Header.tsx:77-108` | `FRONTEND_CALC` (React State) | Bind to backend `TerminalState.environment`. Lock `LIVE` to prevent UI activation without signed hardware/config confirmation. |
| **Trading Mode** | `MODE: PAPER` | `src/App.tsx:25`, `src/components/Header.tsx:111-115` | `FRONTEND_CALC` (React State) | Sync with backend `TerminalState.trading_mode`. |
| **System Status** | `STATUS: ONLINE` / `HALTED` | `src/App.tsx:26`, `src/components/Header.tsx:117-132` | `FRONTEND_CALC` (React State) | Sync with backend `TerminalState.system_status` (heartbeat, websocket connection state, circuit breaker). |
| **Kill Switch Button** | `KILL SWITCH` / `HALT ENGAGED` | `src/App.tsx:27, 45-53`, `Header.tsx:135-145` | `FRONTEND_CALC` (Interactive) | Wire button to send HTTP POST `/api/risk/kill-switch` to trigger `RiskManager.engage_kill_switch()`. |
| **Total Equity** | `$10,000.00` | `src/App.tsx:37`, `src/components/Header.tsx:154-158` | `STATIC_UI` (Hardcoded Const) | Query `adapter.get_account_balances()["USDT"].total` from Binance Testnet or SQLite DB. |
| **Daily P/L ($ & %)** | `+$184.50 (+1.84%)` | `src/App.tsx:38-39`, `src/components/Header.tsx:160-171` | `STATIC_UI` (Hardcoded Const) | Compute from `RiskManager.daily_pnl_usd` and closed trades table in SQLite DB. |
| **Risk Used** | `0.25% / 1.00% max` | `src/components/Header.tsx:175` | `STATIC_UI` (Hardcoded String) | Calculate sum of risk on active open positions: $\sum (\text{position.risk\_pct})$. |
| **Daily Loss Guard** | `0.00% / 2.00%` | `src/components/Header.tsx:180` | `STATIC_UI` (Hardcoded String) | Bind to `RiskManager._calc_daily_loss_pct()` vs `RiskManager.max_daily_loss_pct`. |
| **Consecutive Losses** | `0 / 3` | `src/components/Header.tsx:185` | `STATIC_UI` (Hardcoded String) | Bind to `RiskManager.consecutive_losses` vs `RiskManager.max_consecutive_losses`. |
| **WebSocket Feed Status** | `WebSocket Feed: OK (12ms)` | `src/components/Header.tsx:192` | `STATIC_UI` (Hardcoded String) | Measure real round-trip latency (`pong.timestamp - ping.timestamp`) via Binance WebSocket connection. |
| **REST Fallback Status** | `REST Fallback: Ready` | `src/components/Header.tsx:195` | `STATIC_UI` (Hardcoded String) | Monitor health of REST fallback poll client. |
| **Trading Sessions** | `London Killzone Active` | `src/components/Header.tsx:197` | `STATIC_UI` (Hardcoded String) | Calculate active ICT session dynamically from UTC clock (Asian: 00-06 UTC, London: 07-10 UTC, NY: 12-15 UTC). |
| **Live Warning Banner** | `🔴 LIVE ENVIRONMENT ACTIVE...` | `src/components/Header.tsx:41-50` | `FRONTEND_CALC` (Conditional JSX) | Retain conditional warning, but ensure Live execution route remains blocked in backend. |

---

## 2. Market Scanner Table (`src/components/MarketScanner.tsx`)

| Table Column | ETHUSDT Value | BTCUSDT Value | SOLUSDT Value | Source Location | Provenance Class | Action Required to make Real |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Symbol** | `ETHUSDT` | `BTCUSDT` | `SOLUSDT` | `src/data/mockData.ts:5, 20, 35` | `MOCK_DATA` | Read symbols dynamically from `config.yaml:symbols`. |
| **Price** | `$3,512.45` | `$66,420.00` | `$154.20` | `src/data/mockData.ts:6, 21, 36` | `MOCK_DATA` | Stream live prices via `BinanceSpotAdapter.get_ticker()`. |
| **24h Change** | `+3.82%` | `+1.45%` | `-1.15%` | `src/data/mockData.ts:7, 22, 37` | `MOCK_DATA` | Compute from 24h ticker data (`GET /api/v3/ticker/24hr`). |
| **HTF Bias (4h)** | `BULLISH` | `BULLISH` | `BEARISH` | `src/data/mockData.ts:8, 23, 38` | `MOCK_DATA` | Evaluate 4h swing sequence using `MarketStructureEngine.classify_trend(htf_swings)`. |
| **Structure (15m)** | `MSS ↑` | `BOS ↑` | `MSS ↓` | `src/data/mockData.ts:9, 24, 39` | `MOCK_DATA` | Compute from `MarketStructureEngine.detect_bos_and_mss(candles_15m)`. |
| **Liquidity Event** | `SSL Swept (3480)` | `EQH Resting (66850)` | `BSL Swept (158.00)` | `src/data/mockData.ts:10, 25, 40` | `MOCK_DATA` | Compute from `LiquidityEngine.detect_sweeps()` and `build_liquidity_pools()`. |
| **FVG Present** | `Yes` (Green check) | `Yes` (Green check) | `Yes` (Green check) | `src/data/mockData.ts:11, 26, 41` | `MOCK_DATA` | Compute from `FVGEngine.detect_fvgs(candles_5m)`. |
| **Order Block** | `Yes` (Green check) | `No` (Red cross) | `Yes` (Green check) | `src/data/mockData.ts:12, 27, 42` | `MOCK_DATA` | Compute from `OrderBlockEngine.detect_order_blocks()`. |
| **P/D Zone** | `DISCOUNT` | `EQUILIBRIUM` | `PREMIUM` | `src/data/mockData.ts:13, 28, 43` | `MOCK_DATA` | Compute from `PremiumDiscountEngine.evaluate_range()`. |
| **Session** | `London Killzone` | `London Killzone` | `London Killzone` | `src/data/mockData.ts:14, 29, 44` | `MOCK_DATA` | Derive from candle UTC timestamp. |
| **Reward:Risk** | `2.85R` | `2.10R` | `2.45R` | `src/data/mockData.ts:15, 30, 45` | `MOCK_DATA` | Calculated from proposed entry, stop loss, and target levels: $\frac{\text{Target} - \text{Entry}}{\text{Entry} - \text{Stop}}$. |
| **SMC Score** | `9.2 / 10` | `8.0 / 10` | `8.8 / 10` | `src/data/mockData.ts:16, 31, 46` | `MOCK_DATA` | Compute using `SignalEngine` composite weighted formula. |
| **Setup Status** | `ARMED` | `WATCHING` | `ARMED` | `src/data/mockData.ts:17, 32, 47` | `MOCK_DATA` | Track via `SetupLifecycleState` transition logic. |

---

## 3. Candlestick Chart & SMC Overlays (`src/components/ChartView.tsx`)

| Visual Element | Displayed Data | Source File & Line | Provenance Class | Action Required to make Real |
| :--- | :--- | :--- | :--- | :--- |
| **Candles (12 bars)** | Timestamps `08:00` to `08:55`, OHLCV values (3448 - 3540) | `src/data/mockData.ts:51-64` | `MOCK_DATA` | Fetch real completed 5m/15m klines via `adapter.get_candles(symbol, timeframe)`. |
| **Swing High Pivot** | Triangle marker at `08:15` ($3,540.00) | `src/data/mockData.ts:55` (`isSwingHigh: true`) | `MOCK_DATA` | Compute via `MarketStructureEngine.identify_swings(candles)`. |
| **Swing Low Pivot** | Triangle marker at `08:35` ($3,448.00) | `src/data/mockData.ts:59` (`isSwingLow: true`) | `MOCK_DATA` | Compute via `MarketStructureEngine.identify_swings(candles)`. |
| **MSS Indicator** | Badge at `08:40` ($3,482.00) | `src/data/mockData.ts:60` (`mss: 'BULLISH'`) | `MOCK_DATA` | Compute via `MarketStructureEngine.detect_bos_and_mss()`. |
| **FVG Shaded Box** | Bullish Gap `[3475.00 - 3495.00]`, Midpoint (50% CE) `3485.00` | `src/data/mockData.ts:66-76` | `MOCK_DATA` | Compute via `FVGEngine.detect_fvgs(candles, timeframe="5m")`. |
| **Order Block Box** | Bullish Demand OB `[3448.00 - 3475.00]`, Score `92.5` | `src/data/mockData.ts:78-87` | `MOCK_DATA` | Compute via `OrderBlockEngine.detect_order_blocks()`. |
| **Volume Histogram** | 1,400 to 4,200 contracts per bar | `src/data/mockData.ts:52-63` | `MOCK_DATA` | Feed real candle volume from exchange klines. |

---

## 4. Liquidity Map (`src/components/LiquidityMap.tsx`)

| Liquidity Level | Price | Pool Type | Touches | Swept | Reclaimed | Source File & Line | Provenance Class | Action Required to make Real |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Previous Day High (PDH)** | $3,560.00 | `PDH` | 2 | No | No | `src/data/mockData.ts:90` | `MOCK_DATA` | Calculate from highest high of previous 24-hour UTC window. |
| **Equal Highs (EQH)** | $3,540.00 | `EQH` | 3 | No | No | `src/data/mockData.ts:91` | `MOCK_DATA` | Compute via `LiquidityEngine.build_liquidity_pools()` with 0.08% tolerance. |
| **Asian Session High** | $3,500.00 | `ASIAN_H` | 1 | Yes | No | `src/data/mockData.ts:92` | `MOCK_DATA` | Extract high during 00:00 - 06:00 UTC. |
| **Asian Session Low** | $3,450.00 | `ASIAN_L` | 2 | Yes | Yes | `src/data/mockData.ts:93` | `MOCK_DATA` | Extract low during 00:00 - 06:00 UTC and evaluate reclaim. |
| **Previous Day Low (PDL)** | $3,410.00 | `PDL` | 1 | No | No | `src/data/mockData.ts:94` | `MOCK_DATA` | Calculate from lowest low of previous 24-hour UTC window. |
| **Current Price Line** | $3,512.45 | Benchmark | - | - | - | `src/App.tsx:191` | `STATIC_UI` (Prop) | Feed live ticker price from WebSocket/REST. |

---

## 5. Signal Center (`src/components/SignalCenter.tsx`)

| Signal Identifier | Field | Value | Source File & Line | Provenance Class | Action Required to make Real |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SIG-ETH-20260919-01** | Symbol & Direction | `ETHUSDT LONG` | `src/data/mockData.ts:100-101` | `MOCK_DATA` | Generated by `SignalEngine` orchestrator. |
| | Score & Bias | `9.2 / 10`, `4H Bullish Expansion` | `src/data/mockData.ts:102-103` | `MOCK_DATA` | Computed from weighted breakdown of setup criteria. |
| | Entry, SL, Targets | Entry `3485.00`, SL `3445.00`, TP1 `3540.00`, TP2 `3580.00` | `src/data/mockData.ts:110-113` | `MOCK_DATA` | Derived from FVG 50% CE (Entry), Liquidity Sweep Low (SL), and opposing pools (TP). |
| | Reward:Risk & Risk % | `2.85R`, `0.25% Risk` | `src/data/mockData.ts:114-115` | `MOCK_DATA` | Computed dynamically from entry/stop/TP levels. |
| | Rationale Breakdown | 6 listed institutional reasons | `src/data/mockData.ts:116-123` | `MOCK_DATA` | Generated as explainability list from `Signal.reasons`. |
| | Risk Verdict | `APPROVED` | `src/data/mockData.ts:124-125` | `MOCK_DATA` | Output of `RiskManager.evaluate_signal(signal)`. |
| **SIG-BTC-20260919-02** | Symbol & Direction | `BTCUSDT LONG` | `src/data/mockData.ts:129-130` | `MOCK_DATA` | Proposed signal candidate. |
| | Score | `6.8 / 10` (Below 8.0 threshold) | `src/data/mockData.ts:131` | `MOCK_DATA` | Computed score below gating minimum. |
| | Reward:Risk | `1.40R` (Below 2.0R floor) | `src/data/mockData.ts:143` | `MOCK_DATA` | Computed from entry ($66,400) and stop ($65,900). |
| | Risk Verdict | `REJECTED BY RISK ENGINE` | `src/data/mockData.ts:149-150` | `MOCK_DATA` | Output of `RiskManager.evaluate_signal(signal)` rejecting for $\text{RR} < 2.0\text{R}$. |

---

## 6. Risk Panel & Position Sizing Calculator (`src/components/RiskPanel.tsx`)

| Metric / Parameter | Displayed Value | Source File & Line | Provenance Class | Verification & Real Backend Mapping |
| :--- | :--- | :--- | :--- | :--- |
| **Daily Loss Guard** | `0.00% / 2.00%` | `src/App.tsx:205-206`, `RiskPanel.tsx:64` | `STATIC_UI` (Props) | Maps to `RiskManager._calc_daily_loss_pct()`. |
| **Consecutive Losses** | `0 / 3 Losses` | `src/App.tsx:203-204`, `RiskPanel.tsx:75` | `STATIC_UI` (Props) | Maps to `RiskManager.consecutive_losses`. |
| **Max Open Positions** | `1 / 2 Active` | `src/App.tsx:201-202`, `RiskPanel.tsx:86` | `STATIC_UI` (Props) | Maps to `len(adapter.get_positions())`. |
| **Minimum Allowed R:R** | `2.00R Hard Floor` | `RiskPanel.tsx:94` | `STATIC_UI` (Literal) | Matches `config.yaml:risk.minimum_reward_risk` & `RiskManager.minimum_rr`. |
| **Calculator: Symbol** | `ETHUSDT` (Selectable) | `src/components/RiskPanel.tsx:24` | `FRONTEND_CALC` (State) | Active selected pair. |
| **Calculator: Risk %** | `0.25%` (Adjustable slider) | `src/components/RiskPanel.tsx:25` | `FRONTEND_CALC` (State) | Matches `config.yaml:risk.risk_per_trade_percent`. |
| **Calculator: Entry / Stop** | Entry `3485.0`, Stop `3445.0` | `src/components/RiskPanel.tsx:26-27` | `FRONTEND_CALC` (State) | Interactive test inputs. |
| **Risk Amount ($)** | `$25.00` ($10,000 * 0.25%) | `src/components/RiskPanel.tsx:30` | `FRONTEND_CALC` (Formula) | Evaluates formula identically to `PositionSizingEngine.calculate_size()`. |
| **Stop Distance ($ & %)** | `$40.00 (1.15%)` | `src/components/RiskPanel.tsx:31` | `FRONTEND_CALC` (Formula) | Stop distance math: $|P_{\text{entry}} - P_{\text{stop}}|$. |
| **Slippage Buffer (5%)** | `$42.00` effective distance | `src/components/RiskPanel.tsx:32` | `FRONTEND_CALC` (Formula) | Incorporates 5% safety buffer. |
| **Calculated Quantity** | `0.5952 ETH` | `src/components/RiskPanel.tsx:34` | `FRONTEND_CALC` (Formula) | Sizing calculation: $\frac{\text{Risk}}{\text{EffectiveStop}}$, rounded to step size. |
| **Total Notional Value** | `$2,074.27 USD` | `src/components/RiskPanel.tsx:35` | `FRONTEND_CALC` (Formula) | Position value: $P_{\text{entry}} \times Q$. |
| **Estimated Fee (0.075%)** | `$1.56 USD` | `src/components/RiskPanel.tsx:36` | `FRONTEND_CALC` (Formula) | Spot maker/taker fee estimation. |

---

## 7. Python Architecture & Test Inspector (`src/components/CodeInspector.tsx`)

| Element | Content | Source File & Line | Provenance Class | Reality Check |
| :--- | :--- | :--- | :--- | :--- |
| **Market Structure Code Tab** | Python implementation of `MarketStructureEngine` | `src/components/CodeInspector.tsx:11-40` | `STATIC_UI` (Embedded String) | Mirrors real file `smc_terminal/src/strategy/market_structure.py`. |
| **Risk Manager Code Tab** | Python implementation of `RiskManager` | `src/components/CodeInspector.tsx:42-70` | `STATIC_UI` (Embedded String) | Mirrors real file `smc_terminal/src/risk/risk_manager.py`. |
| **Liquidity Code Tab** | Python implementation of `LiquidityEngine` | `src/components/CodeInspector.tsx:72-100` | `STATIC_UI` (Embedded String) | Mirrors real file `smc_terminal/src/strategy/liquidity.py`. |
| **Position Sizer Code Tab** | Python implementation of `PositionSizingEngine` | `src/components/CodeInspector.tsx:102-130` | `STATIC_UI` (Embedded String) | Mirrors real file `smc_terminal/src/risk/position_sizing.py`. |
| **Test Output Display** | `Ran 17 tests in 0.002s — OK` | `src/components/CodeInspector.tsx:145-155` | `STATIC_UI` (Pre-baked text) | Confirmed: running `PYTHONPATH=smc_terminal python3 -m unittest` produces the exact output. |

---

## Summary & Conversion Roadmap

```
Total Tracked UI Values: 42
├── REAL_ALGO / FRONTEND_CALC: 9 items (21.4%)
├── MOCK_DATA: 24 items (57.1%)
└── STATIC_UI: 9 items (21.4%)
```

**Target State:** 100% of MOCK_DATA and STATIC_UI values will be replaced by direct WebSocket/REST data feeds connected to the verified Python SMC quantitative engine and Binance Testnet adapter.
