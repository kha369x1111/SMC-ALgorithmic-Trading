/**
 * SMC Algorithmic Trading Terminal - Web Companion Types
 */

export type EnvironmentMode = 'demo' | 'testnet' | 'live';
export type TradingMode = 'paper' | 'execution';
export type SystemStatus = 'ONLINE' | 'HALTED' | 'CIRCUIT_BROKEN' | 'DATA_STALE';

export interface ScannerRow {
  symbol: string;
  price: number;
  change24h: number;
  htfBias: 'BULLISH' | 'BEARISH' | 'RANGING';
  structure: 'BOS ↑' | 'BOS ↓' | 'MSS ↑' | 'MSS ↓' | 'RANGING';
  liquidity: string;
  fvg: boolean;
  orderBlock: boolean;
  pdZone: 'DISCOUNT' | 'PREMIUM' | 'EQUILIBRIUM';
  session: string;
  rr: number;
  score: number;
  status: 'ARMED' | 'WATCHING' | 'REJECTED' | 'FILLED';
}

export interface CandleData {
  index: number;
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  isSwingHigh?: boolean;
  isSwingLow?: boolean;
  bos?: 'BULLISH' | 'BEARISH';
  mss?: 'BULLISH' | 'BEARISH';
}

export interface FVGOverlay {
  direction: 'BULLISH' | 'BEARISH';
  top: number;
  bottom: number;
  midpoint: number;
  startIndex: number;
  endIndex: number;
  mitigated: boolean;
}

export interface OrderBlockOverlay {
  direction: 'BULLISH' | 'BEARISH';
  top: number;
  bottom: number;
  startIndex: number;
  endIndex: number;
  score: number;
}

export interface LiquidityPoolData {
  id: string;
  price: number;
  type: 'EQH' | 'EQL' | 'BSL' | 'SSL' | 'PDH' | 'PDL' | 'ASIAN_H' | 'ASIAN_L';
  strength: number;
  touches: number;
  swept: boolean;
  reclaimed: boolean;
  distancePct: number;
}

export interface SignalItem {
  id: string;
  symbol: string;
  direction: 'LONG' | 'SHORT';
  score: number;
  htfBias: string;
  liquidityEvent: string;
  structureEvent: string;
  fvgStatus: string;
  obStatus: string;
  pdZone: 'DISCOUNT' | 'PREMIUM';
  session: string;
  entryPrice: number;
  stopLoss: number;
  tp1: number;
  tp2: number;
  rr: number;
  riskPct: number;
  reasons: string[];
  verdict: 'APPROVED' | 'REJECTED';
  verdictReason: string;
}

export interface OrderRecord {
  client_order_id: string;
  exchange_order_id?: string;
  symbol: string;
  side: string;
  order_type: string;
  quantity: number;
  price?: number;
  stop_price?: number;
  status: string;
  executed_qty: number;
  avg_price: number;
  fee_paid: number;
  timestamp: number;
  updated_at?: string;
}

export interface RiskEventRecord {
  id: number;
  event_type: string;
  description: string;
  value?: number;
  threshold?: number;
  timestamp: number;
}

export interface PositionRecord {
  id?: number;
  symbol: string;
  side: string;
  entry_price: number;
  current_price: number;
  quantity: number;
  stop_loss: number;
  take_profit: number;
  unrealized_pnl: number;
  pnl_percent: number;
  status: string;
  opened_at: number;
}

export interface TradeRecord {
  id: number;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  realized_pnl: number;
  return_pct: number;
  entry_time: number;
  exit_time: number;
  exit_reason: string;
}

export interface DBRecordsResponse {
  signals: any[];
  orders: OrderRecord[];
  positions: PositionRecord[];
  trades: TradeRecord[];
  riskEvents: RiskEventRecord[];
  systemEvents: any[];
}

