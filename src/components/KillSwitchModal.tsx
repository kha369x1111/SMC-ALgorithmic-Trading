import React from 'react';
import { AlertTriangle, ShieldAlert, X } from 'lucide-react';

interface KillSwitchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isCurrentlyActive: boolean;
}

export const KillSwitchModal: React.FC<KillSwitchModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isCurrentlyActive,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 font-mono">
      <div className="bg-neutral-900 border border-neutral-700 rounded-lg max-w-md w-full p-6 shadow-2xl flex flex-col gap-4 text-neutral-100">
        <div className="flex items-center justify-between pb-2 border-b border-neutral-800">
          <div className="flex items-center gap-2 text-red-400 font-bold text-sm uppercase">
            <ShieldAlert className="w-5 h-5" />
            <span>Emergency Kill Switch Confirmation</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-neutral-800 text-neutral-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="text-xs text-neutral-300 leading-relaxed flex flex-col gap-2">
          {isCurrentlyActive ? (
            <p>
              The system is currently <strong>HALTED</strong>. Disengaging the Kill Switch will re-enable
              order routing if all market state and risk criteria pass.
            </p>
          ) : (
            <>
              <p>
                Engaging the <strong>EMERGENCY KILL SWITCH</strong> will immediately:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-neutral-400">
                <li>Halt all order routing and execution pipes immediately.</li>
                <li>Block any pending and incoming trade signals.</li>
                <li>Prevent new position initiation.</li>
                <li>Log the emergency event to SQLite and disk with timestamp.</li>
              </ul>
            </>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-neutral-800 hover:bg-neutral-700 text-xs font-semibold text-neutral-300 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-4 py-2 rounded text-xs font-bold text-white transition-colors cursor-pointer ${
              isCurrentlyActive
                ? 'bg-emerald-700 hover:bg-emerald-600'
                : 'bg-red-600 hover:bg-red-500'
            }`}
          >
            {isCurrentlyActive ? 'Disengage & Resume' : 'CONFIRM EMERGENCY HALT'}
          </button>
        </div>
      </div>
    </div>
  );
};
