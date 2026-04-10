import { API_BASE_URL } from './client';

function parseEventBlock(block) {
  const normalized = block.replace(/\r\n/g, '\n').trim();
  if (!normalized) {
    return null;
  }

  let type = 'message';
  const dataLines = [];

  for (const line of normalized.split('\n')) {
    if (line.startsWith('event:')) {
      type = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  return {
    type,
    data: JSON.parse(dataLines.join('\n')),
  };
}

export async function streamChat(payload, { onEvent } = {}) {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.detail || 'Streaming request failed');
  }

  if (!response.body) {
    throw new Error('Streaming is not supported in this browser.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split('\n\n');
    buffer = blocks.pop() ?? '';

    for (const block of blocks) {
      const event = parseEventBlock(block);
      if (event) {
        onEvent?.(event);
      }
    }
  }

  const tailEvent = parseEventBlock(buffer);
  if (tailEvent) {
    onEvent?.(tailEvent);
  }
}
