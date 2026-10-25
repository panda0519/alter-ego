import { useEffect, useRef, useState } from 'react';
import type { Batch, Method } from './data/models';
import { askAssistant, suggestedQuestions } from './data/assistant';
import type { AssistantSource } from './data/assistant';
import AquaMark from './AquaMark';

export interface ChatMessage { id: number; role: 'user' | 'assistant'; text: string; source?: AssistantSource }

function inlineText(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) return <strong key={index}>{part.slice(2, -2)}</strong>;
    return part.replaceAll('**', '');
  });
}

function sentences(text: string): string[] {
  const parts = text.split(/(?<=\.)\s+/).map(part => part.trim()).filter(Boolean);
  return parts.length ? parts : [text];
}

function ChatBody({ text }: { text: string }) {
  const blocks: { kind: 'p' | 'ul'; lines: string[] }[] = [];
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line) continue;
    const bullet = line.startsWith('- ') ? line.slice(2) : null;
    const pieces = sentences(bullet ?? line);
    const last = blocks.at(-1);
    if (bullet && last?.kind === 'ul') last.lines.push(...pieces);
    else if (bullet) blocks.push({ kind: 'ul', lines: pieces });
    else pieces.forEach(piece => blocks.push({ kind: 'p', lines: [piece] }));
  }
  if (!blocks.length) return null;
  return <div className="chat-body">
    {blocks.map((block, index) => block.kind === 'ul'
      ? <ul key={index}>{block.lines.map((line, lineIndex) => <li key={lineIndex}>{inlineText(line)}</li>)}</ul>
      : <p key={index}>{inlineText(block.lines[0])}</p>)}
  </div>;
}

export default function AquaChat({ batch, stationId, chartMethod, messages, onMessages }: {
  batch: Batch;
  stationId?: string;
  chartMethod?: Method;
  messages: ChatMessage[];
  onMessages: (messages: ChatMessage[]) => void;
}) {
  const [draft, setDraft] = useState('');
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState<string | null>(null);
  const logEnd = useRef<HTMLDivElement>(null);
  const contextMethod = batch.agent_context.meta.default_method;
  const live = messages.some(message => message.source === 'agent37');
  const answered = messages.some(message => message.role === 'assistant');
  const chips = answered ? [
    stationId ? `Explain ${stationId}.` : 'Explain this station.',
    'How do the reconstruction methods compare?',
    'What are the limitations of this synthetic export?',
  ] : suggestedQuestions;
  useEffect(() => {
    logEnd.current?.scrollIntoView({ block: 'nearest' });
  }, [messages, pending]);
  async function send(question: string) {
    const text = question.trim();
    if (!text || pending) return;
    const next = [...messages, { id: Date.now(), role: 'user' as const, text }];
    onMessages(next);
    setDraft('');
    setPending(true);
    setFailed(null);
    try {
      const reply = await askAssistant(batch, { question: text, stationId, chartMethod });
      onMessages([...next, { id: Date.now() + 1, role: 'assistant', text: reply.text, source: reply.source }]);
    } catch {
      setFailed(text);
    } finally {
      setPending(false);
    }
  }
  return <div className="aqua-chat">
    <div className="aqua-chat-head">
      <AquaMark idPrefix="aqua-panel" />
      <div>
        <h2 id="aqua-title">Aqua — Groundwater Assistant</h2>
        <p>Station {stationId ?? 'none'} · default method {contextMethod}</p>
        {live ? <p className="status-pill">Powered by Agent37</p> : <p className="status-pill">Verified export briefing. Agent37 instance gr7nnwqxgf is not answering from this page.</p>}
      </div>
    </div>
    {chartMethod && chartMethod !== contextMethod && <p className="caveat" role="status">The chart uses {chartMethod}. Aqua explains the exported default method {contextMethod} and will not invent facts for the chart method.</p>}
    <div className="suggestion-row">
      {chips.map(question => <button key={question} type="button" onClick={() => send(question)} disabled={pending}>{question}</button>)}
    </div>
    <div className="chat-log" role="log" aria-live="polite" aria-relevant="additions">
      {messages.length === 0 && <p className="empty-state">Ask about the selected station, inspection priorities, the graph, or the limits of this export.</p>}
      {messages.map(message => <article key={message.id} className={`chat-message ${message.role}`}>
        <p className="chat-kicker">{message.role === 'user' ? 'You' : message.source === 'agent37' ? 'Aqua · Agent37' : 'Aqua · export briefing'}</p>
        <ChatBody text={message.text} />
      </article>)}
      {pending && <p className="typing-indicator" role="status">Aqua is reading {stationId ?? 'the selected station'}…</p>}
      {failed && <p role="alert">The question could not be answered. <button type="button" onClick={() => send(failed)}>Retry</button></p>}
      <div ref={logEnd} />
    </div>
    <form onSubmit={event => { event.preventDefault(); void send(draft); }}>
      <label htmlFor="aqua-question">Ask Aqua</label>
      <div className="chat-compose">
        <input id="aqua-question" value={draft} maxLength={400} onChange={event => setDraft(event.target.value)} placeholder="Ask about this groundwater export" />
        <button type="submit" disabled={pending || !draft.trim()}>Send</button>
      </div>
    </form>
  </div>;
}
