import React, { useState } from 'react';
import { LiquidityPoolData } from '../types';
import { Shield, Eye, CheckCircle2, AlertCircle } from 'lucide-react';

interface LiquidityMapProps {
  symbol: string;
  currentPrice: number;
  pools: LiquidityPoolData[];
}

export const LiquidityMap: React.FC<LiquidityMapProps> = ({
  symbol,
  currentPrice,
  pools,
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');

  const filteredPools = pools.filter((p) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'HIGHS')
      return ['BSL', 'EQH', 'PDH', 'ASIAN_H'].includes(p.type);
    if (filterType === 'LOWS')
      return ['SSL', 'EQL', 'PDL', 'ASIAN_L'].includes(p.type);
    if (filterType === 'SWEPT') return p.swept;
    return true;
  });

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden flex flex-col">
      <div className="px-4 py-3 border-b border-neutral-800 flex flex-wrap items-center justify-between gap-3 bg-neutral-950/60">
        <div>
          <h2 className="text-sm font-bold text-neutral-100 uppercase tracking-wide font-mono flex items-center gap-2">
            <Shield className="w-4 h-4 text-cyan-400" />
            Resting Liquidity & Pool Map ({symbol})
          </h2>
          <p className="text-[11px] text-neutral-400 font-mono">
            Tracks resting stops, equal highs/lows, prior session extremes, and sweep confirmations
          </p>
        </div>

        <div className="flex items-center gap-1 bg-neutral-900 border border-neutral-800 rounded p-0.5 text-xs font-mono">
          {['ALL', 'HIGHS', 'LOWS', 'SWEPT'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                filterType === t
                  ? 'bg-neutral-800 text-white font-bold'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 flex flex-col gap-3">
        {filteredPools.map((pool) => {
          const isAbove = pool.price >= currentPrice;
          return (
            <div
              key={pool.id}
              className={`p-3 rounded-lg border flex items-center justify-between font-mono text-xs transition-colors ${
                pool.swept
                  ? pool.reclaimed
                    ? 'bg-emerald-950/20 border-emerald-500/40 text-emerald-300'
                    : 'bg-neutral-950/40 border-neutral-800 text-neutral-400'
                  : isAbove
                  ? 'bg-neutral-950 border-cyan-500/20 text-cyan-300'
                  : 'bg-neutral-950 border-amber-500/20 text-amber-300'
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    pool.type.includes('H')
                      ? 'bg-cyan-950 border border-cyan-500/40 text-cyan-300'
                      : 'bg-amber-950 border border-amber-500/40 text-amber-300'
                  }`}
                >
                  {pool.type}
                </span>

                <div>
                  <span className="font-bold text-sm text-neutral-100">
                    ${pool.price.toFixed(2)}
                  </span>
                  <span className="text-[11px] text-neutral-400 ml-2">
                    ({pool.distancePct >= 0 ? '+' : ''}
                    {pool.distancePct.toFixed(2)}% from price)
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4 text-[11px]">
                <span className="text-neutral-400">
                  Touches:{' '}
                  <span className="text-neutral-200 font-bold">{pool.touches}</span>
                </span>
                <span className="text-neutral-400">
                  Strength:{' '}
                  <span className="text-neutral-200 font-bold">
                    {'★'.repeat(Math.round(pool.strength))}
                  </span>
                </span>

                {pool.swept ? (
                  <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[10px] bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/40">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {pool.reclaimed ? 'SWEPT & RECLAIMED' : 'SWEPT'}
                  </span>
                ) : (
                  <span className="text-[10px] bg-neutral-800 px-2 py-0.5 rounded text-neutral-300">
                    RESTING LIQUIDITY
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
