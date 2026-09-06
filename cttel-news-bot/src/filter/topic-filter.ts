import type { RawArticle } from '../feeds/article.js';
import { isIranSource } from '../config/sources.js';

const APPLE_SOURCES = new Set(['9to5mac', 'macrumors']);

const COMPUTER_BLOCK_PATTERNS: RegExp[] = [
  /\blaptop/i,
  /\bchromebook/i,
  /\bn(?:ote)?book\b(?!check)/i,
  /\bdesktop\b/i,
  /\bgaming\s+pc/i,
  /\bgaming\s+laptop/i,
  /\bmechanical\s+keyboard/i,
  /\bkeyboard\b/i,
  /\bkeycap/i,
  /\bmonitor\b/i,
  /\bgraphics\s+card/i,
  /\bvideo\s+card/i,
  /\bgpu\b/i,
  /\bgeforce\s+rtx/i,
  /\bradeon\s+rx/i,
  /\bmotherboard/i,
  /\bmacbook/i,
  /\bimac\b/i,
  /\bmac\s+mini/i,
  /\bmac\s+studio/i,
  /\bmac\s+pro/i,
  /\bthinkpad/i,
  /\bsurface\s+laptop/i,
  /\bdell\s+xps/i,
  /\bwindows\s+pc/i,
  /\bwindows\s+11\s+pc/i,
  /\bpc\s+build/i,
  /\bgaming\s+chair/i,
  /\bsteam\s+deck/i,
  /\bplaystation/i,
  /\bxbox/i,
  /\bnintendo\s+switch/i,
  /\bsmart\s+tv/i,
  /\btelevision/i,
  /\btv\b/i,
  /\bprinter/i,
  /\brouter\b/i,
  /\bmodem\b/i,
  /\bserver\b/i,
  /\bdatacenter/i,
  /\bdata\s+center/i,
  /\bnas\b/i,
  /\bhard\s+drive/i,
  /\bwebcam\b/i,
  /\bpc\s+case/i,
  /\btower\s+case/i,
  /\bworkstation/i,
  /\bmini\s+pc/i,
  /\bnuc\b/i,
  /\bcpu\b/i,
  /\bprocessor\s+for\s+pc/i,
  /\bintel\s+core\s+i[3579]/i,
  /\bamd\s+ryzen\s+[579]/i,
  /\bgta\s+[ivx]+/i,
  /\bpc\s+game/i,
  /\bwindows\s+laptop/i,
];

const ALLOWED_FOREIGN_BRAND_PATTERNS: RegExp[] = [
  /\bsamsung\b/i,
  /\bgalaxy\b/i,
  /\bexynos\b/i,
  /\bapple\b/i,
  /\biphone/i,
  /\bipad/i,
  /\bairpods/i,
  /\bapple\s+watch/i,
  /\bwatch\s+ultra/i,
  /\bxiaomi\b/i,
  /\bredmi\b/i,
  /\bpoco\b/i,
  /\bnothing\s+phone\b/i,
  /\bnothing\s+phone\s*\(/i,
  /\bhonor\b/i,
];

const APPLE_MOBILE_PATTERNS: RegExp[] = [
  /\biphone/i,
  /\bipad/i,
  /\bapple\s+watch/i,
  /\bairpods/i,
  /\bvision\s+pro/i,
  /\bios\s+\d+/i,
  /\bipados/i,
  /\bwatchos/i,
];

export interface TopicFilterResult {
  allowed: boolean;
  reason:
    | 'iran-source'
    | 'foreign-brand'
    | 'apple-mobile'
    | 'blocked-computer'
    | 'no-allowed-brand';
}

function articleText(article: RawArticle): string {
  return `${article.title} ${article.summary}`.toLowerCase();
}

function matchesAny(text: string, patterns: RegExp[]): boolean {
  return patterns.some((pattern) => pattern.test(text));
}

export function evaluateArticleTopic(article: RawArticle): TopicFilterResult {
  if (isIranSource(article.sourceId)) {
    return { allowed: true, reason: 'iran-source' };
  }

  const text = articleText(article);

  if (matchesAny(text, COMPUTER_BLOCK_PATTERNS)) {
    return { allowed: false, reason: 'blocked-computer' };
  }

  if (APPLE_SOURCES.has(article.sourceId)) {
    if (matchesAny(text, APPLE_MOBILE_PATTERNS)) {
      return { allowed: true, reason: 'apple-mobile' };
    }
    return { allowed: false, reason: 'no-allowed-brand' };
  }

  if (matchesAny(text, ALLOWED_FOREIGN_BRAND_PATTERNS)) {
    return { allowed: true, reason: 'foreign-brand' };
  }

  return { allowed: false, reason: 'no-allowed-brand' };
}

export function isRelevantArticle(article: RawArticle): boolean {
  return evaluateArticleTopic(article).allowed;
}
