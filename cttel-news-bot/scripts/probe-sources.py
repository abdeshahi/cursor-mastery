#!/usr/bin/env python3
import re
import subprocess
import sys

FEEDS = {
    'ict-gov': 'https://ict.gov.ir/fa/news/rss',
    'cra-rss1': 'https://www.cra.ir/fa/news/rss',
    'cra-rss2': 'https://www.cra.ir/fa/news/allnews/rss',
    'tci-rss1': 'https://www.tci.ir/fa/news/rss',
    'isti-rss1': 'https://www.isti.ir/fa/news/rss',
    'isti-rss2': 'https://www.isti.ir/fa/rss/allnews',
    'tasnim14': 'https://www.tasnimnews.com/fa/rss/feed/14',
    'fars-sci': 'https://www.farsnews.ir/rss/science',
    'gsm-feed': 'https://gsm.ir/feed',
    'gsm-rss': 'https://gsm.ir/rss',
    'mobile-rss': 'https://www.mobile.ir/news/rss.aspx',
    'citna': 'https://www.citna.ir/rss',
    'zoomit': 'https://www.zoomit.ir/feed/',
    'digiato': 'https://digiato.com/feed/',
    'peivast': 'https://peivast.com/feed/',
    'ictnews': 'https://ictnews.ir/feed/',
    'irna-sci': 'https://www.irna.ir/rss?plq=sci',
    'isna-sci': 'https://www.isna.ir/rss/tp/science',
    'mehr-sci': 'https://www.mehrnews.com/rss?k=sci',
    'khabar-ict': 'https://www.khabaronline.ir/rss/tp/ict',
    'asreertebat': 'https://asreertebat.com/feed/',
}

PAGES = {
    'gsm-news': 'https://gsm.ir/news',
    'fars-science-page': 'https://www.farsnews.ir/science',
    'tasnim-page': 'https://www.tasnimnews.com/fa/service/14',
    'cra-page': 'https://www.cra.ir/fa/news',
    'tci-page': 'https://www.tci.ir/fa/news',
    'isti-page': 'https://www.isti.ir/fa/news',
}


def curl(url: str, headers_only: bool = False) -> str:
    cmd = ['curl', '-sL', '--max-time', '25']
    if headers_only:
        cmd.append('-I')
    cmd.append(url)
    return subprocess.check_output(cmd, text=True, errors='ignore')


def main() -> None:
    print('=== FEEDS ===')
    for name, url in FEEDS.items():
        try:
            headers = curl(url, headers_only=True)
            codes = [line.split()[1] for line in headers.splitlines() if line.upper().startswith('HTTP')]
            code = codes[-1] if codes else '???'
            content_type = next(
                (line.split(':', 1)[1].strip() for line in headers.splitlines() if line.lower().startswith('content-type:')),
                '',
            )
            body = curl(url)[:100].replace('\n', ' ')
            print(f'{name}\t{code}\t{content_type}\t{body}\t{url}')
        except Exception as error:
            print(f'{name}\tERR\t{error}\t{url}')

    print('\n=== PAGES ===')
    for name, url in PAGES.items():
        try:
            html = curl(url)
            rss_links = sorted(set(re.findall(r'href="([^"]*(?:rss|feed)[^"]*)"', html, re.I)))
            print(f'{name}\t{url}\t{rss_links[:8]}')
        except Exception as error:
            print(f'{name}\tERR\t{error}\t{url}')


if __name__ == '__main__':
    main()
