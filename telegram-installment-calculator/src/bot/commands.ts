import type { Telegraf } from 'telegraf';
import type { BotContext } from './types.js';

const BOT_COMMANDS = [
  { command: 'start', description: 'شروع محاسبه اقساط' },
  { command: 'help', description: 'راهنمای استفاده' },
  { command: 'cancel', description: 'لغو عملیات جاری' },
  { command: 'admin', description: 'مدیریت طرح‌ها و تنظیمات (مدیر)' },
] as const;

export async function registerBotCommands(bot: Telegraf<BotContext>): Promise<void> {
  await bot.telegram.setMyCommands([...BOT_COMMANDS]);
}
