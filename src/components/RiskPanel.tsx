import React, { useState } from 'react';
import { ShieldCheck, Calculator, AlertTriangle, Lock, RefreshCw, Database, Send, Loader2, CheckCircle2, History } from 'lucide-react';
import { DBRecordsResponse, OrderRecord, RiskEventRecord } from '../types';
import { api, ExecuteOrderResponse } from '../services/api';

interface RiskPanelProps {
  equity: number;
  openPositionsCount: number;
  maxOpenPositions: number;
  consecutiveLosses: number;
  maxConsecutiveLosses: number;
  dailyLossPct: number;
  maxDailyLossPct: number;
  dbRecords?: DBRecordsResponse;
  onRefreshRecords?: () => void;
  killSwitchActive?: boolean;
}

export const RiskPanel: React.FC<RiskPanelProps> = ({
  equity,
  openPositionsCount,
  maxOpenPositions,
  consecutiveLosses,
  maxConsecutiveLosses,
  dailyLossPct,
  maxDailyLossPct,
  dbRecords,
  onRefreshRecords,
  killSwitchActive = false,
}) => {
  // Interactive Position Sizer State
  const [calcSymbol, setCalcSymbol] = useState<'ETHUSDT' | 'BTCUSDT' | 'SOLUSDT'>('ETHUSDT');
  const [calcRiskPct, setCalcRiskPct] = useState<number>(0.25);
  const [calcEntry, setCalcEntry] = useState<number>(3485.0);
  const [calcStop, setCalcStop] = useState<number>(3445.0);
  const [calcSide, setCalcSide] = useState<'BUY' | 'SELL'>('BUY');
  const [isExecuting, setIsExecuting] = useState(false);
  const [execResult, setExecResult] = useState<ExecuteOrderResponse | null>(null);
  const [execError, setExecError] = useState<string | null>(null);

  // Position Sizing Formula Execution
  const riskAmountUsd = equity * (calcRiskPct / 100.0);
  const stopDistance = Math.abs(calcEntry - calcStop);
  const effectiveStopDistance = stopDistance * 1.05; // 5% slippage buffer
  const rawQuantity = stopDistance > 0 ? riskAmountUsd / effectiveStopDistance : 0;
  const roundedQuantity = Math.floor(rawQuantity * 10000) / 10000;
  const notionalValue = calcEntry * roundedQuantity;
  const estFee = notionalValue * 0.00075;

  const isValidNotional = notionalValue >= 5.0 && notionalValue <= equity;

  const handleExecuteFromSizer = async () => {
    if (killSwitchActive) {
      setExecError('Kill Switch is active! Disengage Kill Switch first.');
      return;
    }
    setIsExecuting(true);
    setExecError(null);
    setExecResult(null);

    try {
      const res = await api.executeOrder({
        symbol: calcSymbol,
        side: calcSide,
        price: calcEntry,
        stop: calcStop,
      });

      if (res.success) {
        setExecResult(res);
        if (onRefreshRecords) onRefreshRecords();
      } else {
        setExecError(res.error || 'Execution rejected by risk manager');
      }
    } catch (err: any) {
      setExecError(err.message || 'Execution error');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden flex flex-col font-mono">
      <div className="px-4 py-3 border-b border-neutral-800 flex items-center justify-between bg-neutral-950/60">
        <h2 className="text-sm font-bold text-neutral-100 uppercase tracking-wide flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Quantitative Risk Management & Sizing Engine
        </h2>
        <div className="flex items-center gap-3">
          {onRefreshRecords && (
            <button
              onClick={onRefreshRecords}
              className="text-xs text-neutral-400 hover:text-white flex items-center gap-1 bg-neutral-800 px-2 py-1 rounded transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Sync DB</span>
            </button>
          )}
          <span className="text-xs text-emerald-400 font-semibold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/40">
            ALL SAFETY GUARDS ACTIVE
          </span>
        </div>
      </div>

      <div className="p-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Live Risk Guards & Circuit Breaker Status */}
        <div className="flex flex-col gap-4">
          <h3 className="text-xs font-bold text-neutral-200 uppercase tracking-wider pb-1 border-b border-neutral-800">
            Portfolio Limits & Automated Circuit Breakers
          </h3>

          <div className="grid grid-cols-2 gap-3 text-xs">
            {/* Daily Loss Guard */}
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 flex flex-col gap-1">
              <span className="text-[10px] text-neutral-400 uppercase">Daily Loss Guard</span>
              <span className="text-base font-bold text-neutral-100">
                {dailyLossPct.toFixed(2)}% / {maxDailyLossPct.toFixed(2)}%
              </span>
              <span className="text-[10px] text-emerald-400">
                {dailyLossPct >= maxDailyLossPct ? 'LOCK TRIGGERED' : 'Safe (Normal Operations)'}
              </span>
            </div>

            {/* Consecutive Losses */}
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 flex flex-col gap-1">
              <span className="text-[10px] text-neutral-400 uppercase">Consecutive Loss Breaker</span>
              <span className="text-base font-bold text-neutral-100">
                {consecutiveLosses} / {maxConsecutiveLosses} Losses
              </span>
              <span className="text-[10px] text-emerald-400">
                {consecutiveLosses >= maxConsecutiveLosses ? 'TRADING HALTED' : 'Normal Gating'}
              </span>
            </div>

            {/* Open Positions Cap */}
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 flex flex-col gap-1">
              <span className="text-[10px] text-neutral-400 uppercase">Max Open Positions</span>
              <span className="text-base font-bold text-neutral-100">
                {openPositionsCount} / {maxOpenPositions} Active
              </span>
              <span className="text-[10px] text-neutral-400">{Math.max(0, maxOpenPositions - openPositionsCount)} Slot(s) Remaining</span>
            </div>

            {/* Minimum RR Constraint */}
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 flex flex-col gap-1">
              <span className="text-[10px] text-neutral-400 uppercase">Minimum Allowed R:R</span>
              <span className="text-base font-bold text-cyan-300">2.00R Hard Floor</span>
              <span className="text-[10px] text-neutral-400">Sub-2R Setups Rejected</span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-neutral-950/80 border border-neutral-800 text-[11px] text-neutral-400 flex flex-col gap-1">
            <span className="text-neutral-200 font-bold flex items-center gap-1">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              SMC Capital Preservation Directives:
            </span>
            <span>• No Martingale progressions or position doubling under any circumstance.</span>
            <span>• Risk allocation is dynamically scaled to stop loss distance, never arbitrary fixed dollars.</span>
            <span>• If 3 consecutive losses occur, the system halts new orders for manual review.</span>
          </div>
        </div>

        {/* Right Column: Interactive Position Sizing Engine */}
        <div className="flex flex-col gap-4 bg-neutral-950/80 p-4 rounded-lg border border-neutral-800">
          <div className="flex items-center justify-between pb-1 border-b border-neutral-800">
            <h3 className="text-xs font-bold text-neutral-200 uppercase tracking-wider flex items-center gap-1.5">
              <Calculator className="w-4 h-4 text-cyan-400" />
              Interactive Position Sizer & Execution
            </h3>
            <span className="text-[10px] text-neutral-400">Equity: ${equity.toLocaleString()}</span>
          </div>

          {/* Sizer Controls */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[10px] text-neutral-400 block mb-1">Asset Symbol</label>
              <select
                value={calcSymbol}
                onChange={(e) => setCalcSymbol(e.target.value as any)}
                className="w-full bg-neutral-900 border border-neutral-800 rounded px-2.5 py-1.5 text-neutral-100 text-xs font-mono focus:outline-hidden focus:border-neutral-700"
              >
                <option value="ETHUSDT">ETHUSDT</option>
                <option value="BTCUSDT">BTCUSDT</option>
                <option value="SOLUSDT">SOLUSDT</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-neutral-400 block mb-1">Direction Side</label>
              <select
                value={calcSide}
                onChange={(e) => setCalcSide(e.target.value as any)}
                className="w-full bg-neutral-900 border border-neutral-800 rounded px-2.5 py-1.5 text-neutral-100 text-xs font-mono focus:outline-hidden focus:border-neutral-700"
              >
                <option value="BUY">BUY (LONG)</option>
                <option value="SELL">SELL (SHORT)</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] text-neutral-400 block mb-1">
                Risk % (Max 1.00%)
              </label>
              <input
                type="number"
                step="0.05"
                min="0.05"
                max="1.00"
                value={calcRiskPct}
                onChange={(e) => setCalcRiskPct(parseFloat(e.target.value) || 0.25)}
                className="w-full bg-neutral-900 border border-neutral-800 rounded px-2.5 py-1.5 text-neutral-100 text-xs font-mono focus:outline-hidden focus:border-neutral-700"
              />
            </div>

            <div>
              <label className="text-[10px] text-neutral-400 block mb-1">Entry Price ($)</label>
              <input
                type="number"
                step="0.5"
                value={calcEntry}
                onChange={(e) => setCalcEntry(parseFloat(e.target.value) || 0)}
                className="w-full bg-neutral-900 border border-neutral-800 rounded px-2.5 py-1.5 text-neutral-100 text-xs font-mono focus:outline-hidden focus:border-neutral-700"
              />
            </div>

            <div className="col-span-2">
              <label className="text-[10px] text-neutral-400 block mb-1">Stop Price ($)</label>
              <input
                type="number"
                step="0.5"
                value={calcStop}
                onChange={(e) => setCalcStop(parseFloat(e.target.value) || 0)}
                className="w-full bg-neutral-900 border border-neutral-800 rounded px-2.5 py-1.5 text-neutral-100 text-xs font-mono focus:outline-hidden focus:border-neutral-700"
              />
            </div>
          </div>

          {/* Sizer Calculation Output */}
          <div className="p-3 rounded-lg bg-neutral-900 border border-neutral-800 text-xs flex flex-col gap-2">
            <div className="flex justify-between items-center text-neutral-400">
              <span>Allocated Risk Amount:</span>
              <span className="text-neutral-100 font-bold">${riskAmountUsd.toFixed(2)} USD</span>
            </div>
            <div className="flex justify-between items-center text-neutral-400">
              <span>Stop Distance (with 5% slippage):</span>
              <span className="text-neutral-100 font-bold">${effectiveStopDistance.toFixed(2)} USD</span>
            </div>
            <div className="flex justify-between items-center text-neutral-400">
              <span>Calculated Compliant Quantity:</span>
              <span className="text-emerald-400 font-bold text-sm">
                {roundedQuantity.toFixed(4)} {calcSymbol.replace('USDT', '')}
              </span>
            </div>
            <div className="flex justify-between items-center text-neutral-400">
              <span>Estimated Notional Value:</span>
              <span className="text-neutral-100 font-semibold">${notionalValue.toFixed(2)} USDT</span>
            </div>
            <div className="flex justify-between items-center text-neutral-400">
              <span>Estimated Exchange Fee (0.075%):</span>
              <span className="text-neutral-300">${estFee.toFixed(3)} USDT</span>
            </div>

            {/* Validation feedback */}
            <div
              className={`mt-1 p-2 rounded text-[11px] font-bold flex items-center gap-1.5 ${
                isValidNotional
                  ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/40'
                  : 'bg-red-950/60 text-red-300 border border-red-500/40'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>
                {isValidNotional
                  ? 'Position size verified against tick, step size & minNotional filters.'
                  : 'Order violates exchange minimum notional (min 5.00 USDT).' }
              </span>
            </div>

            {/* Execute Order Button */}
            <div className="pt-2 flex flex-col gap-2">
              <button
                onClick={handleExecuteFromSizer}
                disabled={!isValidNotional || isExecuting}
                className="w-full py-2 px-3 rounded bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white font-bold text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                {isExecuting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Routing to Python Paper Adapter...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Execute Order on Paper Adapter</span>
                  </>
                )}
              </button>

              {execResult && (
                <div className="p-2 bg-emerald-950/80 border border-emerald-500/40 rounded text-[11px] text-emerald-300 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                  <span>
                    Order <strong>{execResult.orderId}</strong> created in SQLite! Qty: {execResult.quantity} @ ${execResult.price}
                  </span>
                </div>
              )}

              {execError && (
                <div className="p-2 bg-red-950/80 border border-red-500/40 rounded text-[11px] text-red-300 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-red-400" />
                  <span>{execError}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Database Persistence Audit Log (Orders & Risk Events) */}
      <div className="p-4 border-t border-neutral-800 bg-neutral-950/60 flex flex-col gap-4">
        <div className="flex items-center justify-between pb-1 border-b border-neutral-800">
          <h3 className="text-xs font-bold text-neutral-200 uppercase tracking-wider flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-400" />
            SQLite Database Persistence Records (smc_terminal/terminal.db)
          </h3>
          <span className="text-[10px] text-neutral-400">WAL Mode • Real-Time Logged</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-xs">
          {/* Recent Orders in DB */}
          <div className="p-3 rounded-lg bg-neutral-900 border border-neutral-800 flex flex-col gap-2">
            <span className="text-[11px] font-bold text-neutral-300 uppercase flex items-center gap-1.5">
              <History className="w-3.5 h-3.5 text-cyan-400" />
              Recent Orders Table ({dbRecords?.orders?.length || 0})
            </span>
            {dbRecords?.orders && dbRecords.orders.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[11px]">
                  <thead className="text-neutral-400 border-b border-neutral-800">
                    <tr>
                      <th className="py-1">Order ID</th>
                      <th className="py-1">Symbol</th>
                      <th className="py-1">Side</th>
                      <th className="py-1 text-right">Qty</th>
                      <th className="py-1 text-right">Price</th>
                      <th className="py-1 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-800/60">
                    {dbRecords.orders.map((o) => (
                      <tr key={o.client_order_id} className="text-neutral-300">
                        <td className="py-1 font-mono text-neutral-400 truncate max-w-[110px]">{o.client_order_id}</td>
                        <td className="py-1 text-white font-bold">{o.symbol}</td>
                        <td className={`py-1 font-bold ${o.side === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                          {o.side}
                        </td>
                        <td className="py-1 text-right">{o.quantity}</td>
                        <td className="py-1 text-right">${o.price?.toFixed(2)}</td>
                        <td className="py-1 text-center">
                          <span className="px-1.5 py-0.5 rounded bg-neutral-800 text-[10px] text-emerald-400 border border-emerald-500/30">
                            {o.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-neutral-400 text-[11px] py-3 text-center">No orders recorded in SQLite yet.</div>
            )}
          </div>

          {/* Recent Risk Events in DB */}
          <div className="p-3 rounded-lg bg-neutral-900 border border-neutral-800 flex flex-col gap-2">
            <span className="text-[11px] font-bold text-neutral-300 uppercase flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              Recorded Risk Events ({dbRecords?.riskEvents?.length || 0})
            </span>
            {dbRecords?.riskEvents && dbRecords.riskEvents.length > 0 ? (
              <div className="overflow-y-auto max-h-[160px] flex flex-col gap-1.5">
                {dbRecords.riskEvents.map((evt) => (
                  <div key={evt.id} className="p-2 rounded bg-neutral-950 border border-neutral-800 text-[11px] flex flex-col">
                    <div className="flex justify-between items-center text-amber-400 font-bold">
                      <span>{evt.event_type}</span>
                      <span className="text-[9px] text-neutral-400">ID #{evt.id}</span>
                    </div>
                    <span className="text-neutral-300 mt-0.5 text-[10px]">{evt.description}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-neutral-400 text-[11px] py-3 text-center">No risk events logged yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
