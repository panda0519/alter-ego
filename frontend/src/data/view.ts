export type AppView = 'stations' | 'analysis' | 'assistant';

export function selectView(action: AppView | 'analyze'): AppView {
  return action === 'analyze' ? 'analysis' : action;
}
