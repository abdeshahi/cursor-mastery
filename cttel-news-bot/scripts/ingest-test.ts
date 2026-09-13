#!/usr/bin/env node
import { DEFAULT_NEWS_SOURCES, resolveSources } from '../src/config/sources.js';
import { fetchArticlesFromSource } from '../src/feeds/rss-fetcher.js';

async function main(): Promise<void> {
  const sources = resolveSources([]);
  const results: Array<{ source: string; status: 'ok' | 'error'; count: number; error?: string }> = [];

  for (const source of sources) {
    try {
      const articles = await fetchArticlesFromSource(source);
      results.push({ source: source.id, status: 'ok', count: articles.length });
      console.log(`OK  ${source.id.padEnd(18)} ${String(articles.length).padStart(3)} articles  ${source.format ?? 'rss'}  ${source.url}`);
    } catch (error) {
      const message = String(error);
      results.push({ source: source.id, status: 'error', count: 0, error: message });
      console.log(`ERR ${source.id.padEnd(18)}   0 articles  ${source.format ?? 'rss'}  ${source.url}`);
      console.log(`    ${message}`);
    }
  }

  const ok = results.filter((item) => item.status === 'ok' && item.count > 0);
  const empty = results.filter((item) => item.status === 'ok' && item.count === 0);
  const failed = results.filter((item) => item.status === 'error');

  console.log('\n=== Summary ===');
  console.log(`Total configured: ${DEFAULT_NEWS_SOURCES.filter((source) => source.enabled).length}`);
  console.log(`Fetched with articles: ${ok.length}`);
  console.log(`Fetched empty: ${empty.length}`);
  console.log(`Failed: ${failed.length}`);

  if (empty.length > 0) {
    console.log('\nEmpty sources:', empty.map((item) => item.source).join(', '));
  }
  if (failed.length > 0) {
    console.log('\nFailed sources:', failed.map((item) => item.source).join(', '));
  }
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
