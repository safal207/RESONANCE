import test from 'node:test';
import assert from 'node:assert/strict';
import { handleRequest, validatePayload } from '../worker.mjs';

const ORIGIN = 'https://safal207.github.io';
const URL = 'https://collector.example.invalid/';

function validPayload(overrides = {}) {
  return {
    schema_version: 1,
    event: 'meaningful_read',
    path: '/RESONANCE/before-you-let-an-ai-agent-move-money.html',
    language: 'en',
    content_kind: 'article',
    ...overrides,
  };
}

function envRecorder() {
  const writes = [];
  return {
    writes,
    env: {
      RESONANCE_EVENTS: {
        writeDataPoint(point) {
          writes.push(point);
        },
      },
    },
  };
}

function post(payload, headers = {}) {
  return new Request(URL, {
    method: 'POST',
    headers: {
      Origin: ORIGIN,
      'Content-Type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(payload),
  });
}

test('accepts one valid five-field event and writes exactly one aggregate data point', async () => {
  const { env, writes } = envRecorder();
  const response = await handleRequest(post(validPayload()), env);

  assert.equal(response.status, 204);
  assert.equal(response.headers.get('access-control-allow-origin'), ORIGIN);
  assert.deepEqual(writes, [{
    blobs: [
      'meaningful_read',
      '/RESONANCE/before-you-let-an-ai-agent-move-money.html',
      'en',
      'article',
      '1',
    ],
    doubles: [1],
  }]);
});

test('rejects every unexpected field instead of silently widening collection', () => {
  for (const field of ['email', 'name', 'referrer', 'user_agent', 'screen', 'client_timestamp', 'session_id', 'ip']) {
    const result = validatePayload(validPayload({ [field]: 'forbidden' }));
    assert.deepEqual(result, { ok: false, code: 'unexpected_fields' }, field);
  }
});

test('rejects unsupported events, languages, content kinds and schema versions', () => {
  assert.deepEqual(validatePayload(validPayload({ event: 'pageview' })), { ok: false, code: 'invalid_event' });
  assert.deepEqual(validatePayload(validPayload({ language: 'fr' })), { ok: false, code: 'invalid_language' });
  assert.deepEqual(validatePayload(validPayload({ content_kind: 'person' })), { ok: false, code: 'invalid_content_kind' });
  assert.deepEqual(validatePayload(validPayload({ schema_version: 2 })), { ok: false, code: 'unsupported_schema' });
});

test('rejects paths outside RESONANCE and strips no query data because query data is forbidden', () => {
  for (const path of [
    '/',
    '/other/',
    '/RESONANCE/article.html?utm_source=x',
    '/RESONANCE/article.html#section',
    `/RESONANCE/${'x'.repeat(600)}`,
  ]) {
    const result = validatePayload(validPayload({ path }));
    assert.deepEqual(result, { ok: false, code: 'invalid_path' }, path);
  }
});

test('rejects requests from other origins', async () => {
  const { env, writes } = envRecorder();
  const request = post(validPayload(), { Origin: 'https://evil.example' });
  const response = await handleRequest(request, env);

  assert.equal(response.status, 403);
  assert.equal(writes.length, 0);
  assert.equal(response.headers.get('access-control-allow-origin'), null);
});

test('rejects non-json content and malformed json', async () => {
  const { env, writes } = envRecorder();

  const textResponse = await handleRequest(new Request(URL, {
    method: 'POST',
    headers: { Origin: ORIGIN, 'Content-Type': 'text/plain' },
    body: 'hello',
  }), env);
  assert.equal(textResponse.status, 415);

  const jsonResponse = await handleRequest(new Request(URL, {
    method: 'POST',
    headers: { Origin: ORIGIN, 'Content-Type': 'application/json' },
    body: '{not-json',
  }), env);
  assert.equal(jsonResponse.status, 400);
  assert.equal(writes.length, 0);
});

test('rejects oversized bodies', async () => {
  const { env, writes } = envRecorder();
  const oversized = validPayload({ path: `/RESONANCE/${'x'.repeat(3000)}` });
  const response = await handleRequest(post(oversized), env);

  assert.equal(response.status, 413);
  assert.equal(writes.length, 0);
});

test('supports only narrow POST CORS preflight', async () => {
  const { env } = envRecorder();
  const ok = await handleRequest(new Request(URL, {
    method: 'OPTIONS',
    headers: {
      Origin: ORIGIN,
      'Access-Control-Request-Method': 'POST',
      'Access-Control-Request-Headers': 'content-type',
    },
  }), env);
  assert.equal(ok.status, 204);
  assert.equal(ok.headers.get('access-control-allow-origin'), ORIGIN);

  const bad = await handleRequest(new Request(URL, {
    method: 'OPTIONS',
    headers: {
      Origin: ORIGIN,
      'Access-Control-Request-Method': 'GET',
    },
  }), env);
  assert.equal(bad.status, 405);
});

test('fails closed when Analytics Engine binding is absent', async () => {
  const response = await handleRequest(post(validPayload()), {});
  assert.equal(response.status, 503);
});
