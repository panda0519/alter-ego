import { useState } from 'react';
import type { Batch, Method } from './data/models';
import { askAssistant, suggestedQuestions } from './data/assistant';
import type { AssistantSource } from './data/assistant';
import AquaMark from './AquaMark';

export interface ChatMessage { id: number; role: 'user' | 'assistant'; text: string; source?: AssistantSource }

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
  const contextMethod = batch.agent_context.meta.default_method;
  const live = messages.some(message => message.source === 'agent37');
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
        {live ? <p>Powered by Agent37</p> : <p>Verified export briefing. Agent37 instance gr7nnwqxgf is not answering from this page.</p>}
      </div>
    </div>
    {chartMethod && chartMethod !== contextMethod && <p className="caveat" role="status">The chart uses {chartMethod}. Aqua explains the exported default method {contextMethod} and will not invent facts for the chart method.</p>}
    <div className="suggestion-row">
      {suggestedQuestions.map(question => <button key={question} type="button" onClick={() => send(question)} disabled={pending}>{question}</button>)}
    </div>
    <div className="chat-log" role="log" aria-live="polite" aria-relevant="additions">
      {messages.length === 0 && <p className="empty-state">Ask about the selected station, inspection priorities, the graph, or the limits of this export.</p>}
      {messages.map(message => <article key={message.id} className={`chat-message ${message.role}`}>
        <p className="chat-kicker">{message.role === 'user' ? 'You' : message.source === 'agent37' ? 'Aqua · Agent37' : 'Aqua · export briefing'}</p>
        <p>{message.text}</p>
      </article>)}
      {pending && <p role="status">Aqua is reading the export…</p>}
      {failed && <p role="alert">The question could not be answered. <button type="button" onClick={() => send(failed)}>Retry</button></p>}
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
