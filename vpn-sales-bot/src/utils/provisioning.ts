export function marzbanUsernameForOrder(orderId: number): string {
  if (!Number.isSafeInteger(orderId) || orderId <= 0) {
    throw new Error('invalid order id');
  }
  const username = `ct_${orderId}`;
  if (username.length > 32) {
    throw new Error('marzban username exceeds 32 characters');
  }
  return username;
}

export function bytesFromGb(trafficGb: number): number {
  if (!Number.isSafeInteger(trafficGb) || trafficGb <= 0) {
    throw new Error('invalid traffic_gb');
  }
  return trafficGb * 1024 * 1024 * 1024;
}

export function unixSeconds(date: Date): number {
  return Math.floor(date.getTime() / 1000);
}

export function nextExpiry(currentExpire: Date | null, now: Date, durationDays: number): Date {
  if (!Number.isSafeInteger(durationDays) || durationDays <= 0) {
    throw new Error('invalid duration_days');
  }
  const base = currentExpire !== null && currentExpire.getTime() > now.getTime() ? currentExpire : now;
  return new Date(base.getTime() + durationDays * 24 * 60 * 60 * 1000);
}

export function resolveSubscriptionUrl(raw: string, prefix?: string): string {
  const value = raw.trim();
  if (value.length === 0) {
    throw new Error('empty subscription url');
  }
  if (/^https?:\/\//i.test(value)) {
    return value;
  }
  if (prefix === undefined) {
    return value.startsWith('/') ? value : `/${value}`;
  }
  const base = prefix.replace(/\/+$/, '');
  const path = value.startsWith('/') ? value : `/${value}`;
  return `${base}${path}`;
}

export function assignNode(planNode: string | null, defaultNode: string): string {
  const fromPlan = planNode?.trim();
  if (fromPlan !== undefined && fromPlan.length > 0) {
    return fromPlan;
  }
  return defaultNode;
}
