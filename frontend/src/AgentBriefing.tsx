import { useEffect, useRef, useState } from 'react';
import type { Batch, Method } from './data/models';
import { checkBriefingContext, ContextCheckError, publicHttpsUrl } from './data/briefing';

type CheckState = { kind: 'idle' | 'loading' | 'success' } | { kind: ContextCheckError['kind']; message: string };

export default function AgentBriefing({ context, selectedId, method }: { context: Batch['agent_context']; selectedId?: string; method?: Method }) {
  const instance = publicHttpsUrl(import.meta.env.VITE_AGENT37_URL);
  const deployedContext = publicHttpsUrl(import.meta.env.VITE_AGENT_CONTEXT_URL);
  const [check, setCheck] = useState<CheckState>({ kind: 'idle' });
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  const well = context.wells.find(well => well.id === selectedId);
  async function checkContext() {
    pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    if (deployedContext.kind === 'invalid') {
      setCheck({ kind: 'invalid-response', message: 'The configured public context URL is invalid. No request was made.' }); return;
    }
    setCheck({ kind: 'loading' });
    try {
      await checkBriefingContext(context, deployedContext.url, controller.signal);
      if (!controller.signal.aborted) setCheck({ kind: 'success' });
    } catch (error) {
      if (!controller.signal.aborted) setCheck({ kind: error instanceof ContextCheckError ? error.kind : 'network-error', message: error instanceof Error ? error.message : 'Context check failed.' });
    }
  }
  return <section className="panel briefing-panel" aria-labelledby="briefing-title">
    <p className="eyebrow">06 / Briefing</p>
    <h2 id="briefing-title">Agent37 inspection briefing</h2>
    <p className="notice">Optional backup service. No agent response is displayed here. Aqua labels a reply Agent37 only after the proxy returns source agent37. The public static site stays on the export briefing unless that proxy is configured.</p>
    <p>{context.meta.dataset_kind} / artifact_kind={context.meta.artifact_kind}. {context.meta.caption}</p>
    <p>Context as of {context.meta.as_of_date}; generated (UTC) {context.meta.generated_at_utc}. Run: {context.meta.run_id}.</p>
    <p className="briefing-selection" role="status">Dashboard well: {well?.id ?? 'None'}. Dashboard method: {method ?? 'None'}. Agent context method: {context.meta.default_method}.</p>
    {method && method !== context.meta.default_method && <p>The agent context contains the exported default method only. Selecting another chart method does not change that context.</p>}
    {instance.kind === 'configured'
      ? <a className="briefing-launch" href={instance.url} target="_blank" rel="noopener noreferrer">Open Agent37 briefing (new tab)</a>
      : <p role="status">{instance.kind === 'missing' ? 'Agent37 instance is not configured.' : 'Agent37 instance URL is invalid.'} This optional backup is disabled; core dashboard functionality remains available.</p>}
    <p>Use the native hosted conversation. These are suggested questions, not generated answers:</p>
    <ul className="briefing-questions"><li>Which wells should I inspect first?</li><li>{well ? `Explain well ${well.id}` : 'Select a well for an explanation question.'}</li><li>What are the limitations?</li></ul>
    <p>Only summary context is used for briefings. Revealing observations in the chart never adds those readings to agent context. No selection, prompt or credential is sent automatically to Agent37.</p>
    <p>{deployedContext.kind === 'configured' ? 'The context check reads the configured public export URL.' : deployedContext.kind === 'invalid' ? 'The configured context URL is invalid. No context request will be made.' : 'No deployed context URL is configured. The context check reads the local dashboard export only.'}</p>
    <button id="check-agent-context" type="button" disabled={check.kind === 'loading'} onClick={checkContext}>{check.kind === 'loading' ? 'Checking context...' : 'Check briefing context file'}</button>
    <div className="briefing-check" role={check.kind === 'idle' || check.kind === 'loading' || check.kind === 'success' ? 'status' : 'alert'} data-check-state={check.kind}>
      {check.kind === 'idle' && 'Context file has not been checked on demand.'}
      {check.kind === 'loading' && 'Loading and validating the context file...'}
      {check.kind === 'success' && 'Context file check passed. This verifies exported data, not an Agent37 fetch, live response or working integration.'}
      {'message' in check && check.message}
    </div>
  </section>;
}
