import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createCanvas, GlobalFonts, loadImage, type SKRSContext2D } from '@napi-rs/canvas';
import { formatJalali } from './jalali.js';

const require = createRequire(import.meta.url);
const moduleDirectory = path.dirname(fileURLToPath(import.meta.url));
const LETTERHEAD_PATH = path.resolve(moduleDirectory, '../../assets/letterhead.png');

const FONT_FAMILY = 'Vazirmatn';
const FONT_LATIN = 'VazirmatnLatin';

const PAGE_WIDTH = 1055;
const PAGE_HEIGHT = 1491;
const CONTENT = {
  top: 250,
  bottom: 1330,
  left: 75,
  right: 980,
};
const DATE_POSITION = { x: 978, y: 108 };

let fontsRegistered = false;
let letterheadPromise: Promise<Awaited<ReturnType<typeof loadImage>>> | undefined;

function ensureFontsRegistered(): void {
  if (fontsRegistered) {
    return;
  }

  const arabicFontPath = require.resolve(
    '@fontsource/vazirmatn/files/vazirmatn-arabic-400-normal.woff2',
  );
  const latinFontPath = require.resolve(
    '@fontsource/vazirmatn/files/vazirmatn-latin-400-normal.woff2',
  );
  const boldArabicFontPath = require.resolve(
    '@fontsource/vazirmatn/files/vazirmatn-arabic-700-normal.woff2',
  );

  GlobalFonts.registerFromPath(arabicFontPath, FONT_FAMILY);
  GlobalFonts.registerFromPath(latinFontPath, FONT_LATIN);
  GlobalFonts.registerFromPath(boldArabicFontPath, `${FONT_FAMILY}-Bold`);
  fontsRegistered = true;
}

async function loadLetterhead() {
  letterheadPromise ??= loadImage(LETTERHEAD_PATH);
  return letterheadPromise;
}

export interface ExportCardOptions {
  lines: string[];
  createdAt?: Date;
}

interface PageLayout {
  fontSize: number;
  lineHeight: number;
  linesPerPage: number;
}

function computePageLayout(lineCount: number, forceSinglePage: boolean): PageLayout {
  const maxHeight = CONTENT.bottom - CONTENT.top;
  let fontSize = 28;
  let lineHeight = 42;

  while (lineCount * lineHeight > maxHeight && lineHeight > 30) {
    lineHeight -= 2;
    fontSize -= 1;
  }

  let linesPerPage = Math.max(1, Math.floor(maxHeight / lineHeight));

  if (forceSinglePage) {
    linesPerPage = Math.max(linesPerPage, lineCount);
  }

  return { fontSize, lineHeight, linesPerPage };
}

function chunkLines(lines: string[], linesPerPage: number): string[][] {
  const pages: string[][] = [];

  for (let index = 0; index < lines.length; index += linesPerPage) {
    pages.push(lines.slice(index, index + linesPerPage));
  }

  return pages.length === 0 ? [[]] : pages;
}

function drawDate(context: SKRSContext2D, createdAt?: Date): void {
  if (createdAt === undefined) {
    return;
  }

  context.font = `22px "${FONT_FAMILY}", "${FONT_LATIN}", sans-serif`;
  context.fillStyle = '#1a1a1a';
  context.direction = 'rtl';
  context.textAlign = 'right';
  context.textBaseline = 'alphabetic';
  context.fillText(formatJalali(createdAt), DATE_POSITION.x, DATE_POSITION.y);
}

function drawLines(context: SKRSContext2D, lines: string[], layout: PageLayout): void {
  context.font = `${String(layout.fontSize)}px "${FONT_FAMILY}", "${FONT_LATIN}", sans-serif`;
  context.fillStyle = '#172033';
  context.direction = 'rtl';
  context.textAlign = 'right';
  context.textBaseline = 'alphabetic';

  for (const [index, line] of lines.entries()) {
    const isHeading =
      line.includes('نسخه') ||
      line.includes('CTTEL') ||
      line.startsWith('✅') ||
      line.startsWith('❌') ||
      line.startsWith('✓') ||
      line.startsWith('✗');

    if (isHeading) {
      context.font = `${String(layout.fontSize + 2)}px "${FONT_FAMILY}-Bold", "${FONT_FAMILY}", "${FONT_LATIN}", sans-serif`;
    } else {
      context.font = `${String(layout.fontSize)}px "${FONT_FAMILY}", "${FONT_LATIN}", sans-serif`;
    }

    context.fillText(line, CONTENT.right, CONTENT.top + index * layout.lineHeight);
  }
}

async function renderLetterheadPage(
  pageLines: string[],
  layout: PageLayout,
  createdAt?: Date,
): Promise<Buffer> {
  ensureFontsRegistered();
  const letterhead = await loadLetterhead();
  const canvas = createCanvas(PAGE_WIDTH, PAGE_HEIGHT);
  const context = canvas.getContext('2d');

  context.drawImage(letterhead, 0, 0, PAGE_WIDTH, PAGE_HEIGHT);
  drawDate(context, createdAt);
  drawLines(context, pageLines, layout);

  return canvas.toBuffer('image/png');
}

export async function renderExportLetterheadPages(options: ExportCardOptions): Promise<Buffer[]> {
  const layout = computePageLayout(options.lines.length, false);
  const pages = chunkLines(options.lines, layout.linesPerPage);

  return Promise.all(pages.map((pageLines) => renderLetterheadPage(pageLines, layout, options.createdAt)));
}

export async function renderExportCardPng(options: ExportCardOptions): Promise<Buffer> {
  const layout = computePageLayout(options.lines.length, true);
  const [pageLines = []] = chunkLines(options.lines, layout.linesPerPage);
  return renderLetterheadPage(pageLines, layout, options.createdAt);
}
