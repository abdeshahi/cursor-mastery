import type { Context } from 'telegraf';
import type { SessionData } from './context.js';

export interface BotContext extends Context {
  session: SessionData;
}
