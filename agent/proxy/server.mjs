import { createServer } from 'node:http';
import { createAssistantState, handleAssistant } from './assistant-core.mjs';

const port = Number(process.env.PORT || 8787);
const state = createAssistantState();
const env = {
  AGENT37_API_URL: process.env.AGENT37_API_URL,
  AGENT37_API_KEY: process.env.AGENT37_API_KEY,
  AGENT37_MODEL: process.env.AGENT37_MODEL,
  AGENT_CONTEXT_URL: process.env.AGENT_CONTEXT_URL,
  ASSISTANT_DEMO_TOKEN: process.env.ASSISTANT_DEMO_TOKEN,
};

const server = createServer(async (request, response) => {
  const origin = process.env.ASSISTANT_ALLOWED_ORIGIN;
  if (origin) {
    response.setHeader('access-control-allow-origin', origin);
    response.setHeader('vary', 'Origin');
  }
  response.setHeader('access-control-allow-headers', 'content-type, x-demo-token');
  response.setHeader('access-control-allow-methods', 'POST, OPTIONS');
  if (request.method === 'OPTIONS') {
    response.writeHead(204);
    response.end();
    return;
  }
  if (request.url !== '/api/assistant') {
    response.writeHead(404, { 'content-type': 'application/json' });
    response.end(JSON.stringify({ error: 'not_found' }));
    return;
  }
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  const bodyText = Buffer.concat(chunks).toString('utf8').slice(0, 8000);
  const result = await handleAssistant({
    method: request.method,
    bodyText,
    ip: request.socket.remoteAddress,
    token: request.headers['x-demo-token'],
  }, env, state);
  response.writeHead(result.status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  response.end(JSON.stringify(result.payload));
});

server.listen(port, '127.0.0.1', () => {
  console.log(`Assistant proxy listening on http://127.0.0.1:${port}/api/assistant`);
});
