import { CandleData, FVGOverlay, LiquidityPoolData, OrderBlockOverlay, ScannerRow, SignalItem } from '../types';

export const initialScannerData: ScannerRow[] = [
  {
    symbol: 'ETHUSDT',
    price: 3512.45,
    change24h: 3.82,
    htfBias: 'BULLISH',
    structure: 'MSS ↑',
    liquidity: 'SSL Swept (3480)',
    fvg: true,
    orderBlock: true,
    pdZone: 'DISCOUNT',
    session: 'London Killzone',
    rr: 2.85,
    score: 9.2,
    status: 'ARMED',
  },
  {
    symbol: 'BTCUSDT',
    price: 66420.00,
    change24h: 1.45,
    htfBias: 'BULLISH',
    structure: 'BOS ↑',
    liquidity: 'EQH Resting (66850)',
    fvg: true,
    orderBlock: false,
    pdZone: 'EQUILIBRIUM',
    session: 'London Killzone',
    rr: 2.10,
    score: 8.0,
    status: 'WATCHING',
  },
  {
    symbol: 'SOLUSDT',
    price: 154.20,
    change24h: -1.15,
    htfBias: 'BEARISH',
    structure: 'MSS ↓',
    liquidity: 'BSL Swept (158.00)',
    fvg: true,
    orderBlock: true,
    pdZone: 'PREMIUM',
    session: 'London Killzone',
    rr: 2.45,
    score: 8.8,
    status: 'ARMED',
  },
];

export const ethCandles: CandleData[] = [
  { index: 0, time: '08:00', open: 3460, high: 3475, low: 3450, close: 3470, volume: 1400 },
  { index: 1, time: '08:05', open: 3470, high: 3495, low: 3465, close: 3490, volume: 1850 },
  { index: 2, time: '08:10', open: 3490, high: 3520, low: 3485, close: 3515, volume: 2200 },
  { index: 3, time: '08:15', open: 3515, high: 3540, low: 3505, close: 3530, volume: 3100, isSwingHigh: true },
  { index: 4, time: '08:20', open: 3530, high: 3535, low: 3510, close: 3515, volume: 1900 },
  { index: 5, time: '08:25', open: 3515, high: 3520, low: 3490, close: 3495, volume: 2100 },
  { index: 6, time: '08:30', open: 3495, high: 3500, low: 3470, close: 3475, volume: 2800 },
  { index: 7, time: '08:35', open: 3475, high: 3480, low: 3448, close: 3452, volume: 3900, isSwingLow: true }, // Sweep of Asian Low
  { index: 8, time: '08:40', open: 3452, high: 3485, low: 3450, close: 3482, volume: 4200, mss: 'BULLISH' }, // Aggressive Displacement
  { index: 9, time: '08:45', open: 3482, high: 3518, low: 3480, close: 3512, volume: 3800 },
  { index: 10, time: '08:50', open: 3512, high: 3525, low: 3495, close: 3502, volume: 2400 },
  { index: 11, time: '08:55', open: 3502, high: 3515, low: 3498, close: 3512, volume: 1950 },
];

export const ethFVGs: FVGOverlay[] = [
  {
    direction: 'BULLISH',
    top: 3495,
    bottom: 3475,
    midpoint: 3485,
    startIndex: 8,
    endIndex: 11,
    mitigated: false,
  },
];

export const ethOrderBlocks: OrderBlockOverlay[] = [
  {
    direction: 'BULLISH',
    top: 3475,
    bottom: 3448,
    startIndex: 7,
    endIndex: 11,
    score: 92.5,
  },
];

export const ethLiquidityPools: LiquidityPoolData[] = [
  { id: '1', price: 3560.00, type: 'PDH', strength: 3.0, touches: 2, swept: false, reclaimed: false, distancePct: 1.35 },
  { id: '2', price: 3540.00, type: 'EQH', strength: 2.0, touches: 3, swept: false, reclaimed: false, distancePct: 0.78 },
  { id: '3', price: 3500.00, type: 'ASIAN_H', strength: 1.5, touches: 1, swept: true, reclaimed: false, distancePct: -0.35 },
  { id: '4', price: 3450.00, type: 'ASIAN_L', strength: 2.5, touches: 2, swept: true, reclaimed: true, distancePct: -1.78 },
  { id: '5', price: 3410.00, type: 'PDL', strength: 3.0, touches: 1, swept: false, reclaimed: false, distancePct: -2.91 },
];

export const liveSignals: SignalItem[] = [
  {
    id: 'SIG-ETH-20260919-01',
    symbol: 'ETHUSDT',
    direction: 'LONG',
    score: 9.2,
    htfBias: '4H Bullish Expansion',
    liquidityEvent: 'Asian Low (3450) Swept & Reclaimed',
    structureEvent: '15M Bullish MSS confirmed with Close > 3480',
    fvgStatus: '5M Bullish FVG [3475 - 3495] with 50% CE at 3485',
    obStatus: '15M Bullish Demand OB [3448 - 3475] (Score: 92.5)',
    pdZone: 'DISCOUNT',
    session: 'London Killzone (08:45 UTC)',
    entryPrice: 3485.00,
    stopLoss: 3445.00,
    tp1: 3540.00,
    tp2: 3580.00,
    rr: 2.85,
    riskPct: 0.25,
    reasons: [
      'Higher timeframe (4H) in institutional markup phase',
      'Sell-side liquidity resting at Asian Low was swept with immediate reclaim',
      'Market Structure Shift (MSS) confirmed on 15M with candle close above swing high',
      'Strong displacement bar with Body/ATR ratio of 1.45',
      'Entry targeted at 50% Consequent Encroachment (CE) of fresh 5M Fair Value Gap',
      'Dealing range location strictly in Discount (below 50% equilibrium)',
    ],
    verdict: 'APPROVED',
    verdictReason: 'All quantitative risk limits satisfied: R:R 2.85 >= 2.0, Risk 0.25% <= 1.0%, Daily loss within 2% threshold.',
  },
  {
    id: 'SIG-BTC-20260919-02',
    symbol: 'BTCUSDT',
    direction: 'LONG',
    score: 6.8,
    htfBias: '4H Range Expansion',
    liquidityEvent: 'No recent SSL sweep detected',
    structureEvent: '15M Minor BOS without displacement',
    fvgStatus: '15M FVG Present [66200 - 66350]',
    obStatus: 'No fresh high-probability Order Block',
    pdZone: 'PREMIUM',
    session: 'London Open',
    entryPrice: 66400.00,
    stopLoss: 65900.00,
    tp1: 67100.00,
    tp2: 67500.00,
    rr: 1.40,
    riskPct: 0.25,
    reasons: [
      'BOS observed on 15M',
      'Attempted breakout near equal highs',
    ],
    verdict: 'REJECTED',
    verdictReason: 'REJECTED BY RISK ENGINE: Minimum Reward:Risk ratio not met (1.40R < 2.0R), Price is in Premium, Liquidity Sweep missing.',
  },
];
