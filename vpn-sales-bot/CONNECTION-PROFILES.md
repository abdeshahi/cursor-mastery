# Connection Profiles and Iran Field Testing

Status: Phase 1.5 data model and manual selection support. This document does
not declare any protocol universally suitable for Iran.

## Production baseline

Observed on 2026-09-11:

- Marzban 0.8.4
- Xray 26.3.27
- VLESS / TCP / REALITY / `xtls-rprx-vision`
- port 443
- fingerprint `chrome`
- inbound tag `VLESS TCP REALITY`
- current target and generated-link SNI: `www.apple.com`

The migration records this existing inbound as `VLESS Reality baseline`; it
does not modify or restart Marzban/Xray. Xray 26.3.27 warns that Apple/iCloud
targets can increase IP-blocking risk. The target must only be changed after a
controlled replacement test. Port 443 is the current baseline, not a global
claim that 443 is always optimal.

## Compatibility snapshot

| Profile | Marzban 0.8.4 | Xray 26.3.27 | Main client caveat |
|---|---|---|---|
| VLESS TCP REALITY Vision | managed | native | endpoint/SNI and core-version compatibility |
| VLESS TCP TLS | managed | native | requires a valid domain and certificate |
| VLESS WS TLS | managed | native | WS/ALPN fingerprint and reverse-proxy path |
| VLESS XHTTP | partial; test generated links | native | NekoBox/Hiddify behavior varies; do not use Vision over XHTTP |
| Hysteria2 | not user-managed by Marzban | native | UDP/QUIC may be blocked |
| TUIC v5 | not managed | not native | requires a separate sing-box service |
| Shadowsocks | managed | native | prefer SS2022; legacy AEAD has probing/replay weaknesses |

Initial field-test candidates are limited to:

1. the existing Reality baseline;
2. VLESS TCP TLS on an isolated test endpoint;
3. VLESS WS TLS on an isolated test endpoint.

No candidate is enabled automatically.

## Data model

- `nodes`: operational node labels and enable/priority state.
- `connection_profiles`: protocol metadata plus Marzban inbound/proxy
  references. Private keys and credentials must never be stored here.
- `plan_connection_profiles`: profiles allowed for a plan and its single
  default profile.
- `orders.connection_profile_id`: immutable profile selection snapshot for
  provisioning.
- `subscriptions.connection_profile_id`: profile that produced the service.
- `profile_test_results`: coarse, non-personal compatibility observations.

Existing plans, orders, and subscriptions are backfilled to the baseline.
Legacy `plans.marzban_profile` and text `node` columns remain supported.

When one profile is available for a plan, the Persian purchase flow is
unchanged. When multiple enabled profiles are assigned, the customer chooses
one before the order is created. Renewals retain the subscription's existing
profile; they do not silently migrate a Marzban user to another inbound.

## Safely preparing a candidate

1. Use a test node/endpoint. Do not displace the production Reality listener.
2. Confirm server-core and client versions.
3. Prepare the Marzban inbound and validate one non-customer test user.
4. Insert a `connection_profiles` row with `enabled = FALSE`.
5. Verify `marzban_inbound_tag`, `marzban_proxies`, and `marzban_inbounds`
   exactly match Marzban.
6. Attach the profile to selected test plans in `plan_connection_profiles`.
7. Enable it only after an end-to-end provisioning dry run.

Do not store a Reality private key, TLS private key, Marzban password, or API
token in PostgreSQL profile metadata.

## Field-report workflow

Customers can select `گزارش نتیجه اتصال` under their service and report:

- ISP: MCI, Irancell, Rightel, Mobinnet, Shatel, Asiatech, or other;
- network: 4G, 5G, TD-LTE, ADSL, VDSL, fiber, fixed wireless, or other;
- client: v2rayNG, NPV, Hiddify, NekoBox, or other;
- result: connected with download, connected without download, or failed.

No Telegram ID, phone, subscription ID, or precise location is inserted into
`profile_test_results`. Province/city, latency, client version, and failure
stage are nullable for later controlled operator tests.

Ping `-1ms` alone is not treated as a failed tunnel. A report should reflect
whether the client connected and transferred real HTTP data.

Example aggregate query:

```sql
SELECT
  cp.name,
  r.isp,
  r.network_type,
  r.client_app,
  count(*) AS tests,
  count(*) FILTER (WHERE r.connected AND r.download_ok) AS successful_downloads,
  count(*) FILTER (WHERE NOT r.connected) AS connection_failures,
  max(r.tested_at) AS last_tested_at
FROM profile_test_results r
JOIN connection_profiles cp ON cp.id = r.profile_id
GROUP BY cp.name, r.isp, r.network_type, r.client_app
ORDER BY last_tested_at DESC;
```

## Evidence limits

Recent public evidence does not provide a controlled winner across Iranian
ISPs. Relevant references:

- Xray REALITY documentation:
  https://xtls.github.io/en/config/transports/reality.html
- Xray 26.3.27 release:
  https://github.com/XTLS/Xray-core/releases/tag/v26.3.27
- Iran DPI field reports:
  https://github.com/net4people/bbs/issues/628
- Iran network allowlisting research:
  https://github.com/net4people/bbs/issues/630

Every operational conclusion should be recorded as an observation with ISP,
network type, date, profile, client, and result—not as a permanent rule.
