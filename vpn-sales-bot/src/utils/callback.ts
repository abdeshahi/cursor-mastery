export type MenuPage = 'home' | 'buy' | 'services' | 'renew' | 'support';
export type IspCode = 'mci' | 'irancell' | 'rightel' | 'mobinnet' | 'shatel' | 'asiatech' | 'other';
export type NetworkTypeCode = '4g' | '5g' | 'td_lte' | 'adsl' | 'vdsl' | 'fiber' | 'fixed_wireless' | 'other';
export type ClientAppCode = 'v2rayng' | 'npv' | 'hiddify' | 'nekobox' | 'other';
export type TestResultCode = 'ok' | 'no_download' | 'failed';

export type CallbackAction =
  | { type: 'menu'; page: MenuPage }
  | { type: 'plan'; planId: number }
  | { type: 'selectProfile'; planId: number; profileId: number }
  | { type: 'approve'; paymentId: number }
  | { type: 'reject'; paymentId: number }
  | { type: 'renew'; subscriptionId: number }
  | { type: 'serviceQr'; subscriptionId: number }
  | { type: 'renewPlan'; subscriptionId: number; planId: number }
  | { type: 'cancel'; orderId: number }
  | { type: 'testStart'; subscriptionId: number }
  | { type: 'testIsp'; subscriptionId: number; isp: IspCode }
  | { type: 'testNetwork'; subscriptionId: number; isp: IspCode; networkType: NetworkTypeCode }
  | {
      type: 'testApp';
      subscriptionId: number;
      isp: IspCode;
      networkType: NetworkTypeCode;
      clientApp: ClientAppCode;
    }
  | {
      type: 'testResult';
      subscriptionId: number;
      isp: IspCode;
      networkType: NetworkTypeCode;
      clientApp: ClientAppCode;
      result: TestResultCode;
    };

const MENU_PAGES: Record<string, MenuPage> = {
  home: 'home',
  buy: 'buy',
  services: 'services',
  renew: 'renew',
  support: 'support',
};
const ISP_CODES = new Set<IspCode>(['mci', 'irancell', 'rightel', 'mobinnet', 'shatel', 'asiatech', 'other']);
const NETWORK_TYPES = new Set<NetworkTypeCode>([
  '4g',
  '5g',
  'td_lte',
  'adsl',
  'vdsl',
  'fiber',
  'fixed_wireless',
  'other',
]);
const CLIENT_APPS = new Set<ClientAppCode>(['v2rayng', 'npv', 'hiddify', 'nekobox', 'other']);
const TEST_RESULTS = new Set<TestResultCode>(['ok', 'no_download', 'failed']);

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

  if (kind === 'pp') {
    const planId = positiveInt(parts[1]);
    const profileId = positiveInt(parts[2]);
    if (parts.length !== 3 || planId === null || profileId === null) {
      return null;
    }
    return { type: 'selectProfile', planId, profileId };
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

  if (kind === 'q') {
    const subscriptionId = positiveInt(parts[1]);
    if (parts.length !== 2 || subscriptionId === null) {
      return null;
    }
    return { type: 'serviceQr', subscriptionId };
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

  if (kind === 't') {
    const subscriptionId = positiveInt(parts[1]);
    if (parts.length !== 2 || subscriptionId === null) {
      return null;
    }
    return { type: 'testStart', subscriptionId };
  }

  if (kind === 'ti') {
    const subscriptionId = positiveInt(parts[1]);
    const isp = parts[2] as IspCode | undefined;
    if (parts.length !== 3 || subscriptionId === null || isp === undefined || !ISP_CODES.has(isp)) {
      return null;
    }
    return { type: 'testIsp', subscriptionId, isp };
  }

  if (kind === 'tn') {
    const subscriptionId = positiveInt(parts[1]);
    const isp = parts[2] as IspCode | undefined;
    const networkType = parts[3] as NetworkTypeCode | undefined;
    if (
      parts.length !== 4 ||
      subscriptionId === null ||
      isp === undefined ||
      !ISP_CODES.has(isp) ||
      networkType === undefined ||
      !NETWORK_TYPES.has(networkType)
    ) {
      return null;
    }
    return { type: 'testNetwork', subscriptionId, isp, networkType };
  }

  if (kind === 'ta' || kind === 'tr') {
    const subscriptionId = positiveInt(parts[1]);
    const isp = parts[2] as IspCode | undefined;
    const networkType = parts[3] as NetworkTypeCode | undefined;
    const clientApp = parts[4] as ClientAppCode | undefined;
    if (
      subscriptionId === null ||
      isp === undefined ||
      !ISP_CODES.has(isp) ||
      networkType === undefined ||
      !NETWORK_TYPES.has(networkType) ||
      clientApp === undefined ||
      !CLIENT_APPS.has(clientApp)
    ) {
      return null;
    }
    if (kind === 'ta' && parts.length === 5) {
      return { type: 'testApp', subscriptionId, isp, networkType, clientApp };
    }
    const result = parts[5] as TestResultCode | undefined;
    if (kind === 'tr' && parts.length === 6 && result !== undefined && TEST_RESULTS.has(result)) {
      return { type: 'testResult', subscriptionId, isp, networkType, clientApp, result };
    }
    return null;
  }

  return null;
}

export function encodeCallback(action: CallbackAction): string {
  switch (action.type) {
    case 'menu':
      return `m:${action.page}`;
    case 'plan':
      return `p:${action.planId}`;
    case 'selectProfile':
      return `pp:${action.planId}:${action.profileId}`;
    case 'approve':
      return `a:${action.paymentId}`;
    case 'reject':
      return `x:${action.paymentId}`;
    case 'renew':
      return `n:${action.subscriptionId}`;
    case 'serviceQr':
      return `q:${action.subscriptionId}`;
    case 'renewPlan':
      return `rp:${action.subscriptionId}:${action.planId}`;
    case 'cancel':
      return `c:${action.orderId}`;
    case 'testStart':
      return `t:${action.subscriptionId}`;
    case 'testIsp':
      return `ti:${action.subscriptionId}:${action.isp}`;
    case 'testNetwork':
      return `tn:${action.subscriptionId}:${action.isp}:${action.networkType}`;
    case 'testApp':
      return `ta:${action.subscriptionId}:${action.isp}:${action.networkType}:${action.clientApp}`;
    case 'testResult':
      return `tr:${action.subscriptionId}:${action.isp}:${action.networkType}:${action.clientApp}:${action.result}`;
  }
}
