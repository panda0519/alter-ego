import type { Batch } from './models.ts';
import { validateAgentContext } from './loadBatch.ts';

export function publicHttpsUrl(raw: string | undefined): { kind: 'missing' | 'invalid' | 'configured'; url?: string } {
  if (!raw?.trim()) return { kind: 'missing' };
  try {
    const url = new URL(raw.trim());
    if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash
      || !url.hostname.includes('.') || /^[\d.]+$/.test(url.hostname) || url.hostname.includes(':')
      || /\.(local|localhost|internal|test|invalid)$/.test(url.hostname)) return { kind: 'invalid' };
    return { kind: 'configured', url: url.href };
  } catch { return { kind: 'invalid' }; }
}

export class ContextCheckError extends Error {
  kind: 'unavailable' | 'invalid-response' | 'timeout' | 'network-error';
  constructor(kind: ContextCheckError['kind'], message: string) { super(message); this.kind = kind; }
}

export async function checkBriefingContext(expected: Batch['agent_context'], url = '/data/agent_context.json', signal?: AbortSignal, fetcher: typeof fetch = fetch, timeoutMs = 8000) {
  const controller = new AbortController();
  const abort = () => controller.abort();
  signal?.addEventListener('abort', abort, { once: true });
  if (signal?.aborted) controller.abort();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetcher(url, { signal: controller.signal, cache: 'no-store', credentials: 'omit', redirect: 'error' });
    if (!response.ok) throw new ContextCheckError('unavailable', `Context file unavailable (HTTP ${response.status}).`);
    const text = await response.text();
    if (!text.trim()) throw new ContextCheckError('invalid-response', 'The context file is empty.');
    let raw: unknown;
    try { raw = JSON.parse(text); } catch { throw new ContextCheckError('invalid-response', 'The context file is not valid JSON.'); }
    try { return validateAgentContext(raw, expected); }
    catch { throw new ContextCheckError('invalid-response', 'The context file is invalid or does not match the loaded batch. Reload the complete export batch.'); }
  } catch (error) {
    if (signal?.aborted) throw error;
    if (timedOut) throw new ContextCheckError('timeout', 'Context file check timed out. Try again.');
    if (error instanceof ContextCheckError) throw error;
    throw new ContextCheckError('network-error', 'Context file could not be fetched. Check the network or public access permissions.');
  } finally {
    clearTimeout(timer); signal?.removeEventListener('abort', abort);
  }
}
