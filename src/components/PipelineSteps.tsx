import React from 'react';
import {
  Database,
  Search,
  MapPin,
  TrendingUp,
  Flame,
  PieChart,
  Clock,
  Target,
  Award,
  ShieldCheck,
  Send,
  CheckCircle2,
} from 'lucide-react';

export const PipelineSteps: React.FC = () => {
  const steps = [
    { title: 'Data Feed', icon: Database, status: 'complete' },
    { title: 'Liquidity Map', icon: MapPin, status: 'complete' },
    { title: 'Structure (BOS/MSS)', icon: TrendingUp, status: 'complete' },
    { title: 'Displacement', icon: Flame, status: 'complete' },
    { title: 'PD Array (FVG/OB)', icon: PieChart, status: 'complete' },
    { title: 'Session Filter', icon: Clock, status: 'complete' },
    { title: 'Setup Detector', icon: Target, status: 'active' },
    { title: 'Signal Score', icon: Award, status: 'active' },
    { title: 'Risk Guard', icon: ShieldCheck, status: 'gate' },
    { title: 'Execution', icon: Send, status: 'gated' },
    { title: 'Reconciliation', icon: CheckCircle2, status: 'ready' },
  ];

  return (
    <div className="bg-neutral-900 border-b border-neutral-800 px-4 py-2.5 overflow-x-auto">
      <div className="max-w-7xl mx-auto flex items-center gap-2 min-w-[840px]">
        <div className="text-[11px] font-mono uppercase text-neutral-400 font-semibold tracking-wider mr-2 shrink-0">
          SMC Pipeline:
        </div>
        {steps.map((s, idx) => {
          const Icon = s.icon;
          return (
            <React.Fragment key={s.title}>
              <div
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono shrink-0 border transition-all ${
                  s.status === 'complete'
                    ? 'bg-neutral-950/80 border-emerald-500/30 text-emerald-400'
                    : s.status === 'active'
                    ? 'bg-emerald-950/50 border-emerald-400 text-emerald-200 animate-pulse'
                    : s.status === 'gate'
                    ? 'bg-amber-950/40 border-amber-500/40 text-amber-300 font-bold'
                    : 'bg-neutral-950 border-neutral-800 text-neutral-400'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{s.title}</span>
              </div>
              {idx < steps.length - 1 && (
                <span className="text-neutral-700 font-mono text-xs">→</span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
