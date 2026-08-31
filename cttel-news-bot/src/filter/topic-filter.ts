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

/** Hard block for clearly off-topic Iranian news */
const IRAN_BLOCK_PATTERNS: RegExp[] = [
  /موشک/u,
  /پهپاد/u,
  /نظامی/u,
  /جنگ/u,
  /بمباران/u,
  /سپاه/u,
  /ارتش/u,
  /سردار/u,
  /ترامپ/u,
  /بایدن/u,
  /اسرائیل/u,
  /فلسطین/u,
  /اوکراین/u,
  /فوتبال/u,
  /ورزش/u,
  /لیگ/u,
  /سینما/u,
  /فیلم/u,
  /سریال/u,
  /بازیگر/u,
  /کشاورزی/u,
  /دام/u,
  /محیط\s*زیست/u,
  /زلزله/u,
  /سیل/u,
  /شبکه\s*های\s*اجتماعی/u,
  /اینستاگرام/u,
  /فیسبوک/u,
  /توییتر/u,
  /کلاب\s*هاوس/u,
  /trump/i,
  /biden/i,
  /missile/i,
  /war\b/i,
  /football/i,
  /soccer/i,
];

const IRAN_MOBILE_PATTERNS: RegExp[] = [
  /موبایل/u,
  /گوشی/u,
  /تلفن\s*همراه/u,
  /تبلت/u,
  /سیم\s*کارت/u,
  /esim/u,
  /ای\s*سی\s*م/u,
  /smartphone/i,
  /tablet/i,
  /گلکسی/u,
  /آی\s*فون/u,
  /iphone/i,
  /samsung/i,
  /xiaomi/i,
  /redmi/i,
  /poco/i,
  /honor/i,
];

const IRAN_REGISTRY_PATTERNS: RegExp[] = [
  /رجیستر/u,
  /رجیستری/u,
  /ثبت\s*تلفن/u,
  /سامانه\s*همتا/u,
  /\bhwi\b/i,
  /واردات\s*گوشی/u,
  /واردات\s*موبایل/u,
  /registry/u,
];

const IRAN_INTERNET_PATTERNS: RegExp[] = [
  /اینترنت/u,
  /فیلترینگ/u,
  /فیلتر\s*شکن/u,
  /vpn/u,
  /پهنای\s*باند/u,
  /تعرفه\s*اینترنت/u,
  /تعرفه\s*دیتا/u,
  /دیتای\s*موبایل/u,
  /فیبر\s*نوری/u,
  /ftth/u,
  /روستا\s*نم/u,
  /wifi/u,
  /wi-fi/u,
  /وای\s*فای/u,
  /broadband/u,
  /قطع\s*اینترنت/u,
  /سرعت\s*اینترنت/u,
];

const IRAN_OPERATOR_PATTERNS: RegExp[] = [
  /اپراتور/u,
  /همراه\s*اول/u,
  /ایران\s*سل/u,
  /ایرانسل/u,
  /رایتل/u,
  /rightel/i,
  /مخابرات/u,
  /شبکه\s*های\s*ارتباط/u,
  /شبکه\s*همراه/u,
  /شبکه\s*موبایل/u,
  /شبکه\s*نسل/u,
  /\b5g\b/i,
  /\b4g\b/i,
  /\blte\b/i,
  /telecom/u,
];

const IRAN_REGULATORY_PATTERNS: RegExp[] = [
  /وزارت\s*ارتباطات/u,
  /سازمان\s*تنظیم/u,
  /رگولات/u,
  /regulat/u,
  /فناوری\s*اطلاعات/u,
  /\bict\b/i,
];

const IRAN_AI_PATTERNS: RegExp[] = [
  /هوش\s*مصنوعی/u,
  /هوش\s*مک/u,
  /chatgpt/u,
  /چت\s*جی\s*پی\s*تی/u,
  /gemini/u,
  /llm/u,
  /\bai\b/i,
];

export interface TopicFilterResult {
  allowed: boolean;
  reason:
    | 'iran-ict-topic'
    | 'no-iran-ict-topic'
    | 'foreign-brand'
    | 'apple-mobile'
    | 'blocked-computer'
    | 'no-allowed-brand';
}

function articleText(article: RawArticle): string {
  return `${article.title} ${article.summary}`;
}

function matchesAny(text: string, patterns: RegExp[]): boolean {
  return patterns.some((pattern) => pattern.test(text));
}

function evaluateIranTopic(text: string): TopicFilterResult {
  if (matchesAny(text, IRAN_BLOCK_PATTERNS)) {
    return { allowed: false, reason: 'no-iran-ict-topic' };
  }

  const hasMobile = matchesAny(text, IRAN_MOBILE_PATTERNS);
  const hasRegistry = matchesAny(text, IRAN_REGISTRY_PATTERNS);
  const hasInternet = matchesAny(text, IRAN_INTERNET_PATTERNS);
  const hasOperator = matchesAny(text, IRAN_OPERATOR_PATTERNS);
  const hasRegulatory = matchesAny(text, IRAN_REGULATORY_PATTERNS);
  const hasAi = matchesAny(text, IRAN_AI_PATTERNS);

  if (hasMobile || hasRegistry || hasInternet || hasOperator || hasRegulatory) {
    return { allowed: true, reason: 'iran-ict-topic' };
  }

  // AI-only stories must mention mobile/telecom context, not politics or war
  if (hasAi && (hasMobile || hasOperator || hasInternet || hasRegulatory)) {
    return { allowed: true, reason: 'iran-ict-topic' };
  }

  return { allowed: false, reason: 'no-iran-ict-topic' };
}

export function evaluateArticleTopic(article: RawArticle): TopicFilterResult {
  const text = articleText(article);

  if (isIranSource(article.sourceId)) {
    return evaluateIranTopic(text);
  }

  const lowered = text.toLowerCase();

  if (matchesAny(lowered, COMPUTER_BLOCK_PATTERNS)) {
    return { allowed: false, reason: 'blocked-computer' };
  }

  if (APPLE_SOURCES.has(article.sourceId)) {
    if (matchesAny(lowered, APPLE_MOBILE_PATTERNS)) {
      return { allowed: true, reason: 'apple-mobile' };
    }
    return { allowed: false, reason: 'no-allowed-brand' };
  }

  if (matchesAny(lowered, ALLOWED_FOREIGN_BRAND_PATTERNS)) {
    return { allowed: true, reason: 'foreign-brand' };
  }

  return { allowed: false, reason: 'no-allowed-brand' };
}

export function isRelevantArticle(article: RawArticle): boolean {
  return evaluateArticleTopic(article).allowed;
}
