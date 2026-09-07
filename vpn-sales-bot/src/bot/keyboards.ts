import { Markup } from 'telegraf';

import { encodeCallback } from '../utils/callback.js';

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

export function servicesKeyboard(subscriptions: Array<{ id: number; plan_name: string | null; status: string }>) {
  const rows = subscriptions.map((item) => [
    Markup.button.callback(
      `♻️ تمدید ${item.plan_name ?? 'VPN'} (${item.status})`,
      encodeCallback({ type: 'renew', subscriptionId: item.id }),
    ),
  ]);
  rows.push([Markup.button.callback('⬅️ منوی اصلی', encodeCallback({ type: 'menu', page: 'home' }))]);
  return Markup.inlineKeyboard(rows);
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
