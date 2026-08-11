import test from 'node:test';
import assert from 'node:assert/strict';
import { buildDemandGraph, scoreProblemCard, signalLevel } from '../market-os.mjs';

const complete = {
  id: 'RES-004-001',
  synthetic: false,
  workflow: { actor: 'procurement agent', action: 'supplier payment' },
  failure: { scenario: 'unknown commit after timeout', impact: 'duplicate payment' },
  currentSolution: { workaround: 'manual ledger reconciliation' },
  trustRequirement: { invariant: 'one intent produces at most one committed payment' },
  productDiscovery: {
    missingCapability: 'authoritative reconciliation before retry',
    pilotInterest: 'yes',
  },
};

test('complete real problem card scores 10', () => {
  assert.equal(scoreProblemCard(complete), 10);
  assert.equal(signalLevel(10), 'verified-product-request');
});

test('synthetic cards are excluded from market demand metrics', () => {
  const synthetic = { ...complete, id: 'DEMO-001', synthetic: true };
  const graph = buildDemandGraph([synthetic]);
  assert.equal(graph.realSignalCount, 0);
  assert.equal(graph.syntheticExcluded, 1);
  assert.equal(graph.metrics.productSignals, 0);
  assert.deepEqual(graph.clusters, []);
});

test('real cards with the same missing capability cluster together', () => {
  const second = {
    ...complete,
    id: 'RES-004-002',
    failure: { scenario: 'ambiguous provider response', impact: 'duplicate supplier charge' },
    productDiscovery: {
      missingCapability: 'reliable authoritative reconciliation before retry',
      pilotInterest: 'yes',
    },
  };
  const graph = buildDemandGraph([complete, second]);
  assert.equal(graph.realSignalCount, 2);
  assert.equal(graph.metrics.verifiedProductRequests, 2);
  assert.equal(graph.clusters.length, 1);
  assert.equal(graph.clusters[0].count, 2);
});

test('partial signals remain below pilot threshold', () => {
  const partial = {
    id: 'RES-004-003',
    synthetic: false,
    workflow: { actor: 'agent', action: 'refund' },
    failure: { scenario: 'duplicate refund', impact: '' },
    currentSolution: { workaround: '' },
    trustRequirement: {},
    productDiscovery: { missingCapability: '', pilotInterest: 'unknown' },
  };
  assert.equal(scoreProblemCard(partial), 4);
  assert.equal(signalLevel(4), 'problem-signal');
});
