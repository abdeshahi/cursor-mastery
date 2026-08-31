import type { IncomingMessage, ServerResponse } from 'node:http';
import type { ArticleStore } from '../store/article-store.js';
import { renderArticlePage, renderNotFoundPage } from './article-page.js';

const SLUG_PATTERN = /^\/read\/([a-f0-9]{12})$/;

function sendHtml(response: ServerResponse, statusCode: number, html: string): void {
  response.writeHead(statusCode, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'public, max-age=300',
  });
  response.end(html);
}

function sendJson(response: ServerResponse, statusCode: number, payload: unknown): void {
  response.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
  response.end(JSON.stringify(payload));
}

export function createHttpHandler(articleStore: ArticleStore) {
  return async (request: IncomingMessage, response: ServerResponse): Promise<void> => {
    const pathname = new URL(request.url ?? '/', 'http://localhost').pathname;

    if (pathname === '/' || pathname === '/health') {
      sendJson(response, 200, { status: 'ok', service: 'cttel-news-bot' });
      return;
    }

    const match = SLUG_PATTERN.exec(pathname);
    if (match !== null) {
      const slug = match[1];
      if (slug === undefined) {
        sendHtml(response, 404, renderNotFoundPage());
        return;
      }

      const article = await articleStore.get(slug);
      if (article === undefined) {
        sendHtml(response, 404, renderNotFoundPage());
        return;
      }

      sendHtml(response, 200, renderArticlePage(article));
      return;
    }

    sendJson(response, 404, { error: 'not_found' });
  };
}
