import { Markup } from 'telegraf';

import {
  encodeCallback,
  type ClientAppCode,
  type IspCode,
  type NetworkTypeCode,
} from '../utils/callback.js';

export function mainMenu() {
  return Markup.inlineKeyboard([
    [Markup.button.callback('🛒 خرید VPN', encodeCallback({ type: 'menu', page: 'buy' }))],
    [Markup.button.callback('📦 سرویس‌های من', encodeCallback({ type: 'menu', page: 'services' }))],
    [Markup.button.callback('♻️ تمدید سرویس', encodeCallback({ type: 'menu', page: 'renew' }))],
    [Markup.button.callback('🆘 پشتیبانی', encodeCallback({ type: 'menu', page: 'support' }))],
  ]);
}

export function plansKeyboard(
  plans: Array<{
    id: number;
    name: string;
    traffic_gb: number;
    duration_days: number;
    price: number;
    currency: string;
  }>,
) {
  const rows = plans.map((plan) => [
    Markup.button.callback(
      `${plan.name} — ${plan.price.toLocaleString('fa-IR')} ${plan.currency}`,
      encodeCallback({ type: 'plan', planId: plan.id }),
    ),
  ]);
  rows.push([Markup.button.callback('⬅️ منوی اصلی', encodeCallback({ type: 'menu', page: 'home' }))]);
  return Markup.inlineKeyboard(rows);
}

export function profilesKeyboard(
  planId: number,
  profiles: Array<{
    id: number;
    name: string;
    protocol: string;
    transport: string;
    security: string;
  }>,
) {
  const rows = profiles.map((profile) => [
    Markup.button.callback(
      `${profile.name} — ${profile.protocol.toUpperCase()}/${profile.transport.toUpperCase()}/${profile.security.toUpperCase()}`,
      encodeCallback({ type: 'selectProfile', planId, profileId: profile.id }),
    ),
  ]);
  rows.push([Markup.button.callback('⬅️ بازگشت به پلن‌ها', encodeCallback({ type: 'menu', page: 'buy' }))]);
  return Markup.inlineKeyboard(rows);
}

export function renewalPlansKeyboard(
  subscriptionId: number,
  plans: Array<{ id: number; name: string; price: number; currency: string }>,
) {
  const rows = plans.map((plan) => [
    Markup.button.callback(
      `${plan.name} — ${plan.price.toLocaleString('fa-IR')} ${plan.currency}`,
      encodeCallback({ type: 'renewPlan', subscriptionId, planId: plan.id }),
    ),
  ]);
  rows.push([Markup.button.callback('⬅️ منوی اصلی', encodeCallback({ type: 'menu', page: 'home' }))]);
  return Markup.inlineKeyboard(rows);
}

export function servicesKeyboard(
  subscriptions: Array<{
    id: number;
    account_name: string;
    plan_name: string | null;
    status: string;
  }>,
) {
  const rows = subscriptions.flatMap((item) => [
    [
      Markup.button.callback(
        `♻️ شارژ/تمدید ${item.account_name}`,
        encodeCallback({ type: 'renew', subscriptionId: item.id }),
      ),
    ],
    [
      Markup.button.callback(
        `📱 دریافت QR ${item.account_name}`,
        encodeCallback({ type: 'serviceQr', subscriptionId: item.id }),
      ),
    ],
    [
      Markup.button.callback(
        '🧪 گزارش نتیجه اتصال',
        encodeCallback({ type: 'testStart', subscriptionId: item.id }),
      ),
    ],
  ]);
  rows.push([Markup.button.callback('⬅️ منوی اصلی', encodeCallback({ type: 'menu', page: 'home' }))]);
  return Markup.inlineKeyboard(rows);
}

const ISPS: Array<[IspCode, string]> = [
  ['mci', 'همراه اول'],
  ['irancell', 'ایرانسل'],
  ['rightel', 'رایتل'],
  ['mobinnet', 'مبین‌نت'],
  ['shatel', 'شاتل'],
  ['asiatech', 'آسیاتک'],
  ['other', 'سایر'],
];

export function testIspKeyboard(subscriptionId: number) {
  return Markup.inlineKeyboard(
    ISPS.map(([isp, label]) => [
      Markup.button.callback(label, encodeCallback({ type: 'testIsp', subscriptionId, isp })),
    ]),
  );
}

const NETWORK_TYPES: Array<[NetworkTypeCode, string]> = [
  ['4g', '4G'],
  ['5g', '5G'],
  ['td_lte', 'TD-LTE'],
  ['adsl', 'ADSL'],
  ['vdsl', 'VDSL'],
  ['fiber', 'فیبر'],
  ['fixed_wireless', 'بی‌سیم ثابت'],
  ['other', 'سایر'],
];

export function testNetworkKeyboard(subscriptionId: number, isp: IspCode) {
  return Markup.inlineKeyboard(
    NETWORK_TYPES.map(([networkType, label]) => [
      Markup.button.callback(
        label,
        encodeCallback({ type: 'testNetwork', subscriptionId, isp, networkType }),
      ),
    ]),
  );
}

const CLIENT_APPS: Array<[ClientAppCode, string]> = [
  ['v2rayng', 'v2rayNG'],
  ['npv', 'NPV'],
  ['hiddify', 'Hiddify'],
  ['nekobox', 'NekoBox'],
  ['other', 'سایر'],
];

export function testClientKeyboard(
  subscriptionId: number,
  isp: IspCode,
  networkType: NetworkTypeCode,
) {
  return Markup.inlineKeyboard(
    CLIENT_APPS.map(([clientApp, label]) => [
      Markup.button.callback(
        label,
        encodeCallback({ type: 'testApp', subscriptionId, isp, networkType, clientApp }),
      ),
    ]),
  );
}

export function testResultKeyboard(
  subscriptionId: number,
  isp: IspCode,
  networkType: NetworkTypeCode,
  clientApp: ClientAppCode,
) {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback(
        '✅ وصل شد و دانلود داشت',
        encodeCallback({ type: 'testResult', subscriptionId, isp, networkType, clientApp, result: 'ok' }),
      ),
    ],
    [
      Markup.button.callback(
        '⚠️ وصل شد ولی دانلود نداشت',
        encodeCallback({
          type: 'testResult',
          subscriptionId,
          isp,
          networkType,
          clientApp,
          result: 'no_download',
        }),
      ),
    ],
    [
      Markup.button.callback(
        '❌ اصلاً وصل نشد',
        encodeCallback({
          type: 'testResult',
          subscriptionId,
          isp,
          networkType,
          clientApp,
          result: 'failed',
        }),
      ),
    ],
  ]);
}

export function adminReviewKeyboard(paymentId: number) {
  return Markup.inlineKeyboard([
    [
      Markup.button.callback('✅ تأیید', encodeCallback({ type: 'approve', paymentId })),
      Markup.button.callback('❌ رد', encodeCallback({ type: 'reject', paymentId })),
    ],
  ]);
}

export function orderKeyboard(orderId: number) {
  return Markup.inlineKeyboard([
    [Markup.button.callback('انصراف از این سفارش', encodeCallback({ type: 'cancel', orderId }))],
    [Markup.button.callback('⬅️ منوی اصلی', encodeCallback({ type: 'menu', page: 'home' }))],
  ]);
}
