import type { RawArticle } from '../feeds/article.js';

/** Sources that publish almost exclusively mobile content */
const TRUSTED_MOBILE_SOURCES = new Set([
  'gsmarena',
  'android-authority',
  'phonearena',
  'android-police',
  '9to5google',
]);

const APPLE_SOURCES = new Set(['9to5mac', 'macrumors']);

const LAB_SOURCES = new Set(['dxomark']);

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

const MOBILE_ALLOW_PATTERNS: RegExp[] = [
  /\bphone/i,
  /\bsmartphone/i,
  /\bmobile/i,
  /\bhandset/i,
  /\biphone/i,
  /\bipad/i,
  /\bgalaxy/i,
  /\bpixel/i,
  /\bandroid/i,
  /\bios\b/i,
  /\btablet/i,
  /\bfoldable/i,
  /\bflip\s+phone/i,
  /\bsmartwatch/i,
  /\bapple\s+watch/i,
  /\bwatch\s+ultra/i,
  /\bwear\s*os/i,
  /\bearbuds/i,
  /\bearphones/i,
  /\bairpods/i,
  /\bheadphone/i,
  /\bcharger/i,
  /\bpower\s+bank/i,
  /\bphone\s+case/i,
  /\bscreen\s+protector/i,
  /\bsnapdragon/i,
  /\bmediatek/i,
  /\bdimensity/i,
  /\bexynos/i,
  /\bapple\s+silicon/i,
  /\ba\d+\s+chip/i,
  /\b5g\b/i,
  /\besim/i,
  /\bsim\s+card/i,
  /\bcamera\s+phone/i,
  /\bphone\s+camera/i,
  /\bxiaomi/i,
  /\boppo/i,
  /\bvivo/i,
  /\brealme/i,
  /\bhuawei/i,
  /\bhonor/i,
  /\bredmi/i,
  /\bpoco/i,
  /\bnokia/i,
  /\bmotorola/i,
  /\boneplus/i,
  /\bnothing\s+phone/i,
  /\bfitness\s+tracker/i,
  /\bsmart\s+ring/i,
  /\bfitbit/i,
  /\bgimbal/i,
  /\bselfie\s+stick/i,
  /\bwireless\s+charging/i,
  /\bmagsafe/i,
  /\busb-c\s+cable/i,
  /\bfast\s+charging/i,
  /\bbattery\s+life/i,
  /\bdisplay\s+test/i,
  /\bcamera\s+test/i,
  /\bdxomark/i,
  /\bai\b/i,
  /\bartificial\s+intelligence/i,
  /\bchatgpt/i,
  /\bgemini\b/i,
  /\bcopilot/i,
  /\bllm/i,
  /\bmachine\s+learning/i,
  /\bopenai/i,
  /\bdeepseek/i,
  /\bclaude\b/i,
  /\bvision\s+pro/i,
  /\bmeta\s+quest/i,
  /\bar\s+glasses/i,
  /\bsmart\s+glasses/i,
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
  reason: 'trusted-source' | 'mobile-topic' | 'apple-mobile' | 'blocked-computer' | 'no-mobile-topic';
}

function articleText(article: RawArticle): string {
  return `${article.title} ${article.summary}`.toLowerCase();
}

function matchesAny(text: string, patterns: RegExp[]): boolean {
  return patterns.some((pattern) => pattern.test(text));
}

export function evaluateArticleTopic(article: RawArticle): TopicFilterResult {
  const text = articleText(article);

  if (matchesAny(text, COMPUTER_BLOCK_PATTERNS)) {
    return { allowed: false, reason: 'blocked-computer' };
  }

  if (TRUSTED_MOBILE_SOURCES.has(article.sourceId)) {
    return { allowed: true, reason: 'trusted-source' };
  }

  if (APPLE_SOURCES.has(article.sourceId)) {
    if (matchesAny(text, APPLE_MOBILE_PATTERNS)) {
      return { allowed: true, reason: 'apple-mobile' };
    }
    return { allowed: false, reason: 'no-mobile-topic' };
  }

  if (LAB_SOURCES.has(article.sourceId)) {
    if (matchesAny(text, MOBILE_ALLOW_PATTERNS)) {
      return { allowed: true, reason: 'mobile-topic' };
    }
    return { allowed: false, reason: 'no-mobile-topic' };
  }

  if (matchesAny(text, MOBILE_ALLOW_PATTERNS)) {
    return { allowed: true, reason: 'mobile-topic' };
  }

  return { allowed: false, reason: 'no-mobile-topic' };
}

export function isRelevantArticle(article: RawArticle): boolean {
  return evaluateArticleTopic(article).allowed;
}
