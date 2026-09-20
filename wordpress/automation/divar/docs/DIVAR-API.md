# Kenar Divar — Official Open Platform API (CTTEL reference)

Sources (verified from Divar-published SDK docs, not scraped):

- Portal: [kenar.divar.dev](https://kenar.divar.dev/)
- Swagger: linked from Kenar panel («فهرست درخواست‌ها»)
- SDK Post API: [kenar-sdk-javascript/docs/PostApi.md](https://github.com/divar-ir/kenar-sdk-javascript/blob/main/docs/PostApi.md)
- Base URL: **`https://open-api.divar.ir`**

## Authentication

| Mechanism | Usage |
|-----------|--------|
| **API Key** | Header `x-api-key: <KENAR_API_KEY>` (created in Kenar panel → Keys) |
| **OAuth 2.0** | Authorization URL: `https://oauth.divar.ir/oauth2/auth` |
| **Access token** | Header `Authorization: Bearer <ACCESS_TOKEN>` |
| **Token exchange** | `POST https://api.divar.ir/v1/open-platform/oauth/access_token` with `code`, `client_id` (app slug), `client_secret` (API key), `grant_type=authorization_code` |

Store **API key**, **client secret**, **OAuth tokens**, and **business token** only in **n8n Credentials** / secure env — never in git.

## Submit post (create listing)

| Endpoint | Method | API key permission | OAuth scope | Notes |
|----------|--------|-------------------|-------------|--------|
| `/experimental/open-platform/posts/new-v2` | POST | **`SUBMIT_POST`** | — | Provider/business posts; **business token required** in request body per SDK |
| `/experimental/open-platform/user-posts/new` | POST | **`SUBMIT_USER_POST`** | **`SUBMIT_USER_POST`** | User-owned post; JSON schema per category |

CTTEL shop listings should align with Kenar **business** flow (`new-v2` + business token) after Divar approves the use case.

## Status / get post

| Endpoint | Method | Permissions |
|----------|--------|-------------|
| `/v1/open-platform/user-post/{token}` | GET | User post read (see SDK) |
| `/experimental/open-platform/posts/{post_token}/stats` | GET | Stats |

## Update post

| Endpoint | Method | API key | OAuth |
|----------|--------|---------|-------|
| `/v1/open-platform/post/{post_token}` | PUT | **`EDIT_POST`** | `POST_EDIT.post_token` |
| `/v2/open-platform/post/{post_token}` | PUT | **`EDIT_POST`** | `EDIT_USER_POST` or `POST_EDIT.post_token` |

## Close / delete post

| Endpoint | Method | API key | OAuth |
|----------|--------|---------|-------|
| `/v1/open-platform/post/{post_token}` | DELETE | **`DELETE_USER_POST`** | **`DELETE_USER_POST`** |

There is no separate «close» endpoint in the published PostApi list; **delete** or **edit** (e.g. mark unavailable via schema fields) must match your category template — confirm in Swagger for your category.

## Images

| Endpoint | Method | Notes |
|----------|--------|-------|
| `/v2/open-platform/post/upload-urls` | GET | Upload URLs for images/video before submit |
| `/v1/open-platform/post/image-upload-url` | GET | Deprecated |

## Pre-check

| Endpoint | Method | Permissions |
|----------|--------|-------------|
| `/experimental/open-platform/user-posts/can-submit` | GET | `CAN_USER_SUBMIT_POST` / `SUBMIT_USER_POST` |

## CTTEL integration mode

Until CTTEL Kenar app has **`SUBMIT_POST`** (or **`SUBMIT_USER_POST`**) on production keys:

- n8n workflows run with **`DRY_RUN=true`** and **`DIVAR_LIVE_SUBMIT=false`** (default).
- Final Divar JSON is **validated and previewed** only.
- **No live listing** is created without your explicit approval.

## User action (Divar)

1. Register app in [Kenar panel](https://kenar.divar.dev/) (test app first).
2. Open support ticket describing **used phone resale** for CTTEL store (Kenar recommends this before production).
3. Create API key with minimum permissions: `SUBMIT_POST`, `EDIT_POST`, `DELETE_USER_POST`, upload URLs as needed.
4. Obtain **business token** for `new-v2` if using business listings.
5. Complete OAuth for scopes you need (`SUBMIT_USER_POST`, `EDIT_USER_POST`, `DELETE_USER_POST`).
6. Map **category slug** + **city** to official JSON schema from Swagger (category-specific fields).
