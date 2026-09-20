import React, { useState } from 'react';
import { SignalItem } from '../types';
import {
  CheckCircle2,
  XCircle,
  ShieldCheck,
  Award,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Send,
  Loader2,
} from 'lucide-react';
import { api, ExecuteOrderResponse } from '../services/api';

interface SignalCenterProps {
  signals: SignalItem[];
  onOrderExecuted?: () => void;
  killSwitchActive?: boolean;
}

export const SignalCenter: React.FC<SignalCenterProps> = ({
  signals,
  onOrderExecuted,
  killSwitchActive = false,
}) => {
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [execStatus, setExecStatus] = useState<Record<string, ExecuteOrderResponse>>({});
  const [errorMsg, setErrorMsg] = useState<Record<string, string>>({});

  const handleExecute = async (sig: SignalItem) => {
    if (killSwitchActive) {
      setErrorMsg((prev) => ({
        ...prev,
        [sig.id]: 'Kill switch is engaged! Disengage in header before executing orders.',
      }));
      return;
    }

    setExecutingId(sig.id);
    setErrorMsg((prev) => ({ ...prev, [sig.id]: '' }));

    try {
      const res = await api.executeOrder({
        symbol: sig.symbol,
        side: sig.direction === 'LONG' ? 'BUY' : 'SELL',
        price: sig.entryPrice,
        stop: sig.stopLoss,
      });

      if (res.success) {
        setExecStatus((prev) => ({ ...prev, [sig.id]: res }));
        if (onOrderExecuted) onOrderExecuted();
      } else {
        setErrorMsg((prev) => ({
          ...prev,
          [sig.id]: res.error || 'Execution rejected by Risk Engine',
        }));
      }
    } catch (err: any) {
      setErrorMsg((prev) => ({
        ...prev,
        [sig.id]: err.message || 'Execution failed',
      }));
    } finally {
      setExecutingId(null);
    }
  };

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden flex flex-col">
      <div className="px-4 py-3 border-b border-neutral-800 flex items-center justify-between bg-neutral-950/60">
        <div>
          <h2 className="text-sm font-bold text-neutral-100 uppercase tracking-wide font-mono flex items-center gap-2">
            <Award className="w-4 h-4 text-emerald-400" />
            SMC Signal Center & Risk Validation Authority
          </h2>
          <p className="text-[11px] text-neutral-400 font-mono">
            Every setup requires multi-condition score ≥ 8/10 and final immutable approval by Risk Engine
          </p>
        </div>
        <div className="text-xs text-neutral-400 font-mono">
          Minimum Threshold: <span className="text-emerald-400 font-bold">8.0 / 10.0</span>
        </div>
      </div>

      <div className="p-4 flex flex-col gap-4">
        {signals.length === 0 ? (
          <div className="p-8 text-center text-neutral-400 font-mono text-xs">
            No active institutional signals currently meeting the 8.0/10.0 quality threshold.
          </div>
        ) : (
          signals.map((sig) => {
            const isApproved = sig.verdict === 'APPROVED';
            const execution = execStatus[sig.id];
            const error = errorMsg[sig.id];
            const isBusy = executingId === sig.id;

            return (
              <div
                key={sig.id}
                className={`p-4 rounded-lg border font-mono transition-all ${
                  isApproved
                    ? 'bg-neutral-950 border-emerald-500/40 shadow-sm'
                    : 'bg-neutral-950/80 border-red-500/30'
                }`}
              >
                {/* Header row */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-neutral-800">
                  <div className="flex items-center gap-3">
                    <span className="text-base font-bold text-white">{sig.symbol}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold ${
                        sig.direction === 'LONG'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/50'
                          : 'bg-red-950 text-red-400 border border-red-500/50'
                      }`}
                    >
                      {sig.direction}
                    </span>
                    <span className="text-xs bg-neutral-800 px-2 py-0.5 rounded text-neutral-300">
                      {sig.session}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <span className="text-[10px] text-neutral-400 uppercase block">
                        Setup Score
                      </span>
                      <span
                        className={`text-sm font-bold ${
                          sig.score >= 8.0 ? 'text-emerald-400' : 'text-amber-400'
                        }`}
                      >
                        {sig.score.toFixed(1)} / 10.0
                      </span>
                    </div>

                    {/* Verdict Badge */}
                    <div
                      className={`px-3 py-1 rounded text-xs font-bold flex items-center gap-1.5 border ${
                        isApproved
                          ? 'bg-emerald-950 text-emerald-300 border-emerald-500/50'
                          : 'bg-red-950 text-red-300 border-red-500/50'
                      }`}
                    >
                      {isApproved ? (
                        <>
                          <ShieldCheck className="w-4 h-4 text-emerald-400" />
                          <span>APPROVED</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-red-400" />
                          <span>REJECTED</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Execution Levels Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 py-3 border-b border-neutral-800 text-xs">
                  <div>
                    <span className="text-neutral-400 text-[10px] block">LIMIT ENTRY (50% FVG)</span>
                    <span className="text-neutral-100 font-bold">${sig.entryPrice.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-neutral-400 text-[10px] block">STOP LOSS (BEHIND SWEEP)</span>
                    <span className="text-red-400 font-bold">${sig.stopLoss.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-neutral-400 text-[10px] block">TAKE PROFIT 1 (1.5R)</span>
                    <span className="text-emerald-400 font-bold">${sig.tp1.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-neutral-400 text-[10px] block">TAKE PROFIT 2 (LIQ TARGET)</span>
                    <span className="text-emerald-400 font-bold">${sig.tp2.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-neutral-400 text-[10px] block">REWARD : RISK</span>
                    <span className="text-cyan-300 font-bold text-sm">{sig.rr.toFixed(2)}R</span>
                  </div>
                </div>

                {/* SMC Setup Checklist & Rationale */}
                <div className="pt-3">
                  <div className="text-[11px] font-semibold text-neutral-300 mb-1.5 uppercase">
                    Explainable Setup Rationale:
                  </div>
                  <div className="flex flex-col gap-1 text-xs">
                    {sig.reasons.map((reason, i) => (
                      <div key={i} className="flex items-center gap-2 text-neutral-300">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>

                  {/* Risk Verdict Explanation */}
                  <div
                    className={`mt-3 p-2.5 rounded text-xs flex items-start gap-2 border ${
                      isApproved
                        ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200'
                        : 'bg-red-950/30 border-red-500/30 text-red-200'
                    }`}
                  >
                    <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5 text-neutral-400" />
                    <div>
                      <span className="font-bold">Risk Management Engine Decision: </span>
                      <span>{sig.verdictReason}</span>
                    </div>
                  </div>

                  {/* Execution Feedback / Action Button */}
                  <div className="mt-3 pt-3 border-t border-neutral-800/80 flex flex-wrap items-center justify-between gap-3">
                    {execution ? (
                      <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-500/40 px-3 py-1.5 rounded">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>
                          Order <strong className="font-bold text-white">{execution.orderId}</strong> active
                          on Paper Adapter (Qty: {execution.quantity}, Notional: ${execution.notional?.toFixed(2)})
                        </span>
                      </div>
                    ) : error ? (
                      <div className="flex items-center gap-2 text-xs text-red-400 bg-red-950/60 border border-red-500/40 px-3 py-1.5 rounded">
                        <AlertTriangle className="w-4 h-4 shrink-0" />
                        <span>{error}</span>
                      </div>
                    ) : (
                      <div className="text-[11px] text-neutral-400">
                        {isApproved
                          ? 'Signal verified. Sized dynamically with 0.25% equity risk.'
                          : 'Execution blocked by institutional risk rules.'}
                      </div>
                    )}

                    {isApproved && (
                      <button
                        onClick={() => handleExecute(sig)}
                        disabled={isBusy || !!execution}
                        className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-bold bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white transition-colors cursor-pointer"
                      >
                        {isBusy ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Routing to Paper Engine...</span>
                          </>
                        ) : execution ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Executed in SQLite</span>
                          </>
                        ) : (
                          <>
                            <Send className="w-3.5 h-3.5" />
                            <span>Transmit Sized Order</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
