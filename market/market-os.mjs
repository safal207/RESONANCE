function present(value) {
  return typeof value === 'string' ? value.trim().length > 0 : Boolean(value);
}

export function scoreProblemCard(card) {
  let score = 0;
  if (present(card?.workflow?.actor) && present(card?.workflow?.action)) score += 2;
  if (present(card?.failure?.scenario)) score += 2;
  if (present(card?.failure?.impact)) score += 2;
  if (present(card?.currentSolution?.workaround)) score += 1;
  if (present(card?.productDiscovery?.missingCapability)) score += 1;
  if (present(card?.trustRequirement?.invariant) || present(card?.trustRequirement?.verification)) score += 1;
  if (card?.productDiscovery?.pilotInterest === 'yes') score += 1;
  return score;
}

export function signalLevel(score) {
  if (score <= 2) return 'reaction';
  if (score <= 4) return 'problem-signal';
  if (score <= 6) return 'qualified-problem';
  if (score <= 8) return 'product-signal';
  if (score === 9) return 'pilot-candidate';
  return 'verified-product-request';
}

export function normalizeCapability(value = '') {
  return value
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]+/gu, ' ')
    .replace(/\b(automatic|automated|machine-readable|independent|safe|reliable)\b/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function clusterKey(card) {
  const capability = normalizeCapability(card?.productDiscovery?.missingCapability || '');
  if (capability) return capability;
  const scenario = normalizeCapability(card?.failure?.scenario || '');
  return scenario || 'unclassified';
}

function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

export function buildDemandGraph(cards) {
  const realCards = cards.filter((card) => card?.synthetic !== true);
  const clusters = new Map();

  for (const card of realCards) {
    const score = scoreProblemCard(card);
    const key = clusterKey(card);
    const current = clusters.get(key) || { key, cardIds: [], scores: [] };
    current.cardIds.push(card.id);
    current.scores.push(score);
    clusters.set(key, current);
  }

  const clusterList = [...clusters.values()]
    .map((cluster) => ({
      key: cluster.key,
      count: cluster.cardIds.length,
      cardIds: cluster.cardIds,
      medianSignalScore: median(cluster.scores),
    }))
    .sort((a, b) => b.count - a.count || b.medianSignalScore - a.medianSignalScore || a.key.localeCompare(b.key));

  return {
    realSignalCount: realCards.length,
    syntheticExcluded: cards.length - realCards.length,
    clusters: clusterList,
    metrics: {
      qualifiedProblems: realCards.filter((card) => scoreProblemCard(card) >= 5).length,
      productSignals: realCards.filter((card) => scoreProblemCard(card) >= 7).length,
      pilotCandidates: realCards.filter((card) => scoreProblemCard(card) >= 9).length,
      verifiedProductRequests: realCards.filter((card) => scoreProblemCard(card) === 10).length,
    },
  };
}
