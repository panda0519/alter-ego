import type { Batch, Role } from './models.ts';
import { initialSelection } from './selection.ts';
import type { Selection } from './selection.ts';

export type DemoMode = 'sensor-available' | 'simulated-outage' | 'reveal';
export type DemoAction = 'outage' | 'reveal' | 'reset';
export interface WorkspaceState { selection: Selection; mode: DemoMode; chartEpoch: number }
export type WorkspaceAction = { type: 'well'; wellId: string } | { type: 'method'; method: string }
  | { type: 'demo'; action: DemoAction; role?: Role };

export function initialWorkspace(batch: Batch): WorkspaceState {
  return { selection: initialSelection(batch), mode: 'sensor-available', chartEpoch: 0 };
}

export function workspaceReducer(state: WorkspaceState, action: WorkspaceAction): WorkspaceState {
  if (action.type === 'well' || action.type === 'method') {
    const selection = action.type === 'well' ? { ...state.selection, wellId: action.wellId } : { ...state.selection, method: action.method };
    if (selection.wellId === state.selection.wellId && selection.method === state.selection.method) return state;
    return { selection, mode: 'sensor-available', chartEpoch: state.chartEpoch + 1 };
  }
  if (action.role !== 'holdout') return state;
  if (action.action === 'reveal' && state.mode !== 'simulated-outage') return state;
  const mode = action.action === 'reset' ? 'sensor-available' : action.action === 'outage' ? 'simulated-outage' : 'reveal';
  return { ...state, mode, chartEpoch: state.chartEpoch + 1 };
}
