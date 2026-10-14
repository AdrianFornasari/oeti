const { test } = require("node:test");
const assert = require("node:assert/strict");
const snapshot = require("../src/data/mv-hondius.snapshot.json");

test("frozen event has the approved membership set and intact relation endpoints", () => {
  const approved = ['013da99e-5666-4d89-827a-7ce683fa0d02', '4eb9f1fd-d769-4d31-bfb3-a3896f0b0b65', '8683a891-4217-4dfe-b2d6-e34ba28a4ea4', '95799c89-1605-4eb2-9f4d-fc3e76c3a11a', 'dd3474d8-8628-4519-8362-96bae27d5045'].sort();
  assert.equal(snapshot.event.id, 'f3c0aefa-49e9-4553-aa67-ddf5a7cb84f6');
  assert.deepEqual(snapshot.signals.map(s => s.id).sort(), approved);
  assert.deepEqual(snapshot.memberships.map(s => s.signal_id).sort(), approved);
  assert.equal(snapshot.relations.length, 3);
  assert.equal(new Set(snapshot.relations.map(r => r.id)).size, 3);
  for (const relation of snapshot.relations) {
    assert.ok(approved.includes(relation.source_signal_id));
    assert.ok(approved.includes(relation.target_signal_id));
    assert.notEqual(relation.source_signal_id, relation.target_signal_id);
  }
});

test("each signal has source evidence and unknown event dates stay unknown", () => {
  assert.equal(snapshot.evidence.length, 8);
  for (const signal of snapshot.signals) {
    assert.equal(new URL(signal.source_url).origin, 'https://www.argentina.gob.ar');
    assert.ok(snapshot.evidence.some(e => e.signal_id === signal.id && e.excerpt.trim()));
    assert.ok(Number.isFinite(Date.parse(signal.published_at)));
    if (signal.date_precision === 'unknown') assert.equal(signal.occurred_start, null);
  }
  assert.ok(snapshot.evidence.every(e => snapshot.signals.some(s => s.id === e.signal_id)));
});

test("browser snapshot has no credential or raw payload fields and keeps capture provenance", () => {
  assert.deepEqual(snapshot.transaction, { read_only: 'on', isolation: 'repeatable read' });
  assert.equal(snapshot.mode, 'frozen_readonly');
  assert.equal(snapshot.extraction_commit, null);
  assert.ok(Number.isFinite(Date.parse(snapshot.captured_at)));
  const forbidden = /secret|password|token|api.?key|database_url|raw_text|raw_payload|reviewed_by/i;
  function inspect(value) {
    if (Array.isArray(value)) value.forEach(inspect);
    else if (value && typeof value === 'object') for (const [key, child] of Object.entries(value)) {
      assert.ok(!forbidden.test(key), `Unexpected browser field: ${key}`);
      inspect(child);
    }
    else if (typeof value === 'string') assert.ok(!/postgres(?:ql)?:\/\/|eyJ[A-Za-z0-9_-]{30,}\./.test(value));
  }
  inspect(snapshot);
});
