const ALLOWED_ORIGIN = 'https://safal207.github.io';
const MAX_BODY_BYTES = 2048;
const REQUIRED_FIELDS = [
  'schema_version',
  'event',
  'path',
  'language',
  'content_kind',
];
const ALLOWED_EVENTS = new Set([
  'meaningful_read',
  'hot_question_view',
  'workflow_intake_open',
  'verified_workflow_open',
]);
const ALLOWED_LANGUAGES = new Set(['en', 'ru', 'zh-CN']);
const ALLOWED_CONTENT_KINDS = new Set(['article', 'page']);

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '600',
    'Vary': 'Origin',
    'Cache-Control': 'no-store',
  };
}

function jsonError(status, code, origin = '') {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  };
  if (origin === ALLOWED_ORIGIN) Object.assign(headers, corsHeaders(origin));
  return new Response(JSON.stringify({ error: code }), { status, headers });
}

export function validatePayload(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return { ok: false, code: 'invalid_payload' };
  }

  const keys = Object.keys(payload).sort();
  const expected = [...REQUIRED_FIELDS].sort();
  if (keys.length !== expected.length || keys.some((key, index) => key !== expected[index])) {
    return { ok: false, code: 'unexpected_fields' };
  }

  if (payload.schema_version !== 1) {
    return { ok: false, code: 'unsupported_schema' };
  }
  if (!ALLOWED_EVENTS.has(payload.event)) {
    return { ok: false, code: 'invalid_event' };
  }
  if (!ALLOWED_LANGUAGES.has(payload.language)) {
    return { ok: false, code: 'invalid_language' };
  }
  if (!ALLOWED_CONTENT_KINDS.has(payload.content_kind)) {
    return { ok: false, code: 'invalid_content_kind' };
  }
  if (
    typeof payload.path !== 'string' ||
    payload.path.length < '/RESONANCE/'.length ||
    payload.path.length > 512 ||
    !payload.path.startsWith('/RESONANCE/') ||
    payload.path.includes('?') ||
    payload.path.includes('#') ||
    /[\u0000-\u001F\u007F]/.test(payload.path)
  ) {
    return { ok: false, code: 'invalid_path' };
  }

  return { ok: true };
}

export async function handleRequest(request, env) {
  const origin = request.headers.get('Origin') || '';

  if (request.method === 'OPTIONS') {
    if (origin !== ALLOWED_ORIGIN) return jsonError(403, 'origin_not_allowed');
    const requestedMethod = request.headers.get('Access-Control-Request-Method') || '';
    if (requestedMethod !== 'POST') return jsonError(405, 'method_not_allowed', origin);
    return new Response(null, { status: 204, headers: corsHeaders(origin) });
  }

  if (request.method !== 'POST') return jsonError(405, 'method_not_allowed', origin);
  if (origin !== ALLOWED_ORIGIN) return jsonError(403, 'origin_not_allowed');

  const contentType = (request.headers.get('Content-Type') || '').toLowerCase();
  if (!contentType.startsWith('application/json')) {
    return jsonError(415, 'content_type_required', origin);
  }

  const declaredLength = Number(request.headers.get('Content-Length') || 0);
  if (Number.isFinite(declaredLength) && declaredLength > MAX_BODY_BYTES) {
    return jsonError(413, 'payload_too_large', origin);
  }

  let text;
  try {
    text = await request.text();
  } catch {
    return jsonError(400, 'invalid_body', origin);
  }

  if (new TextEncoder().encode(text).byteLength > MAX_BODY_BYTES) {
    return jsonError(413, 'payload_too_large', origin);
  }

  let payload;
  try {
    payload = JSON.parse(text);
  } catch {
    return jsonError(400, 'invalid_json', origin);
  }

  const validation = validatePayload(payload);
  if (!validation.ok) return jsonError(400, validation.code, origin);

  if (!env?.RESONANCE_EVENTS || typeof env.RESONANCE_EVENTS.writeDataPoint !== 'function') {
    return jsonError(503, 'collector_unavailable', origin);
  }

  env.RESONANCE_EVENTS.writeDataPoint({
    blobs: [
      payload.event,
      payload.path,
      payload.language,
      payload.content_kind,
      String(payload.schema_version),
    ],
    doubles: [1],
  });

  return new Response(null, {
    status: 204,
    headers: corsHeaders(origin),
  });
}

export default {
  fetch: handleRequest,
};
