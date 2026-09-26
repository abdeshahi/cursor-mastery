/**
 * Read-only production commerce audit (HTTP only, no writes).
 */
const BASE = 'https://cttel.ir';

async function fetchText(url) {
  const res = await fetch(url, { redirect: 'follow', headers: { 'User-Agent': 'CTTEL-ReadOnly-Audit/1.0' } });
  return { status: res.status, text: await res.text(), headers: Object.fromEntries(res.headers) };
}

function uniq(arr) {
  return [...new Set(arr)];
}

function extractPluginSlugs(html) {
  const slugs = [];
  const re = /wp-content\/plugins\/([^/'"]+)/g;
  let m;
  while ((m = re.exec(html))) slugs.push(m[1]);
  return uniq(slugs).sort();
}

function extractVersions(html) {
  const wc = html.match(/woocommerce[^?]*\?ver=([0-9.]+)/i)?.[1] || html.match(/ver=wc-([0-9.]+)/i)?.[1];
  const wp = html.match(/<meta name="generator" content="WordPress ([0-9.]+)/i)?.[1];
  const theme = html.match(/themes\/([^/]+)\//)?.[1];
  const themeVer = html.match(/themes\/blocksy[^?]*\?ver=([0-9.]+)/)?.[1];
  return { woocommerce: wc, wordpress: wp, theme, themeVer };
}

function gatewayHints(html) {
  const ids = [];
  const patterns = [
    /payment_method_[a-z0-9_-]+/gi,
    /wc_payment_method_[a-z0-9_-]+/gi,
    /id="payment_method_([a-z0-9_-]+)"/gi,
    /data-gateway="([a-z0-9_-]+)"/gi,
  ];
  for (const re of patterns) {
    let m;
    while ((m = re.exec(html))) {
      const id = m[1] || m[0].replace(/^payment_method_/, '');
      if (id && !['payment_method', 'wc_payment_method'].includes(id)) ids.push(id.replace(/^payment_method_/, ''));
    }
  }
  const persian = [];
  for (const name of ['زرین', 'Zarinpal', 'zarinpal', 'آیدی', 'IDPay', 'idpay', 'نکست', 'NextPay', 'nextpay', 'زیبال', 'Zibal', 'ملت', 'Mellat', 'mellat', 'سامان', 'Saman', 'به‌پرداخت', 'Behpardakht', 'Pay.ir', 'payir']) {
    if (html.includes(name)) persian.push(name);
  }
  return { gatewayIds: uniq(ids), nameHints: uniq(persian) };
}

(async () => {
  const pages = ['/', '/shop/', '/cart/', '/checkout/', '/my-account/'];
  const combined = { plugins: [], versions: {}, gatewayHints: { gatewayIds: [], nameHints: [] } };
  const pageMeta = {};

  for (const path of pages) {
    const { status, text, headers } = await fetchText(BASE + path);
    pageMeta[path] = { status, php: headers['x-powered-by'] || headers['X-Powered-By'] || null };
    combined.plugins = uniq([...combined.plugins, ...extractPluginSlugs(text)]);
    const v = extractVersions(text);
    combined.versions = { ...combined.versions, ...Object.fromEntries(Object.entries(v).filter(([, val]) => val)) };
    const g = gatewayHints(text);
    combined.gatewayHints.gatewayIds = uniq([...combined.gatewayHints.gatewayIds, ...g.gatewayIds]);
    combined.gatewayHints.nameHints = uniq([...combined.gatewayHints.nameHints, ...g.nameHints]);
  }

  let rest = null;
  try {
    const r = await fetch(BASE + '/wp-json/');
    rest = await r.json();
  } catch (e) {
    rest = { error: String(e) };
  }

  // Probe common Iranian gateway plugin folders (directory listing blocked → 404/403 only).
  const probeSlugs = [
    'zarinpal-woocommerce-payment-gateway',
    'woocommerce-zarinpal-gateway',
    'wc-zarinpal',
    'persian-woocommerce',
    'persian-woocommerce-sms',
    'woocommerce-ultimate-gift-card',
    'idpay-contact-form-7',
    'woocommerce-idpay-gateway',
    'WC_ZPal',
    'zarinpal-payment-gateway',
    'melli-pay',
    'woo-zibal',
    'zibal-woocommerce',
    'nextpay-woocommerce',
    'wc-mellat-gateway',
    'woocommerce-mellat',
    'saman-epay',
    'behpardakht-woocommerce',
  ];
  const probes = {};
  for (const slug of probeSlugs) {
    const head = await fetch(BASE + `/wp-content/plugins/${slug}/`, { method: 'HEAD' });
    probes[slug] = head.status;
  }

  // WooCommerce Store API (read-only, no cart mutation).
  let storeSettings = null;
  try {
    const sr = await fetch(BASE + '/wp-json/wc/store/v1/cart');
    storeSettings = { cartStatus: sr.status, note: 'GET cart without session' };
  } catch (e) {
    storeSettings = { error: String(e) };
  }

  console.log(
    JSON.stringify(
      {
        base: BASE,
        pageMeta,
        versions: combined.versions,
        pluginsFromAssets: combined.plugins,
        gatewayHints: combined.gatewayHints,
        pluginProbes: probes,
        restNamespaces: rest?.namespaces?.filter((n) => n.includes('wc')) ?? [],
        storeSettings,
      },
      null,
      2
    )
  );
})();
