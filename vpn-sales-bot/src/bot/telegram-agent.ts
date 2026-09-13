import type { Agent } from 'node:http';
import { HttpsProxyAgent } from 'https-proxy-agent';

export function createTelegramAgent(proxyUrl?: string): Agent | undefined {
  if (proxyUrl === undefined) {
    return undefined;
  }
  return new HttpsProxyAgent(proxyUrl);
}
