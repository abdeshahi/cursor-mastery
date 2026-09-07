export type MenuPage = 'home' | 'buy' | 'services' | 'renew' | 'support';

export type CallbackAction =
  | { type: 'menu'; page: MenuPage }
  | { type: 'plan'; planId: number }
  | { type: 'approve'; paymentId: number }
  | { type: 'reject'; paymentId: number }
  | { type: 'renew'; subscriptionId: number }
  | { type: 'renewPlan'; subscriptionId: number; planId: number }
  | { type: 'cancel'; orderId: number };

const MENU_PAGES: Record<string, MenuPage> = {
  home: 'home',
  buy: 'buy',
  services: 'services',
  renew: 'renew',
  support: 'support',
};

function positiveInt(value: string | undefined): number | null {
  if (value === undefined || !/^[1-9]\d{0,15}$/.test(value)) {
    return null;
  }
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

export function parseCallback(data: string): CallbackAction | null {
  if (data.length === 0 || data.length > 64) {
    return null;
  }

  const parts = data.split(':');
  const kind = parts[0];

  if (kind === 'm') {
    const page = parts[1];
    if (parts.length !== 2 || page === undefined) {
      return null;
    }
    const resolved = MENU_PAGES[page];
    if (resolved === undefined) {
      return null;
    }
    return { type: 'menu', page: resolved };
  }

  if (kind === 'p') {
    const planId = positiveInt(parts[1]);
    if (parts.length !== 2 || planId === null) {
      return null;
    }
    return { type: 'plan', planId };
  }

  if (kind === 'a') {
    const paymentId = positiveInt(parts[1]);
    if (parts.length !== 2 || paymentId === null) {
      return null;
    }
    return { type: 'approve', paymentId };
  }

  if (kind === 'x') {
    const paymentId = positiveInt(parts[1]);
    if (parts.length !== 2 || paymentId === null) {
      return null;
    }
    return { type: 'reject', paymentId };
  }

  if (kind === 'n') {
    const subscriptionId = positiveInt(parts[1]);
    if (parts.length !== 2 || subscriptionId === null) {
      return null;
    }
    return { type: 'renew', subscriptionId };
  }

  if (kind === 'rp') {
    const subscriptionId = positiveInt(parts[1]);
    const planId = positiveInt(parts[2]);
    if (parts.length !== 3 || subscriptionId === null || planId === null) {
      return null;
    }
    return { type: 'renewPlan', subscriptionId, planId };
  }

  if (kind === 'c') {
    const orderId = positiveInt(parts[1]);
    if (parts.length !== 2 || orderId === null) {
      return null;
    }
    return { type: 'cancel', orderId };
  }

  return null;
}

export function encodeCallback(action: CallbackAction): string {
  switch (action.type) {
    case 'menu':
      return `m:${action.page}`;
    case 'plan':
      return `p:${action.planId}`;
    case 'approve':
      return `a:${action.paymentId}`;
    case 'reject':
      return `x:${action.paymentId}`;
    case 'renew':
      return `n:${action.subscriptionId}`;
    case 'renewPlan':
      return `rp:${action.subscriptionId}:${action.planId}`;
    case 'cancel':
      return `c:${action.orderId}`;
  }
}
