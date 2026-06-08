# Client Onboarding Checklist

Fill this in at the **start** of the project. Items in **Section 1 (platform
access)** have external approval lead times (days→weeks for Meta App Review /
LinkedIn product access), so kick those off on day one — everything else can be
done in an afternoon.

> 🔒 **Sending us credentials:** never paste tokens or secrets into email or
> chat. Use a password manager share, a one-time secret link (e.g. onetimesecret),
> or enter them yourself in the dashboard's **Accounts → Add manually** screen.
> All tokens are encrypted at rest and are never displayed back.

Legend: ☐ = to do · fill blanks inline.

---

## 0. Project basics

- ☐ Client / brand name: `______________________`
- ☐ Main point of contact (name + email): `______________________`
- ☐ Platforms in scope (tick): ☐ Facebook Page  ☐ LinkedIn  ☐ Threads
- ☐ Package: ☐ Basic  ☐ Standard  ☐ Premium  (see SERVICE.md)
- ☐ Target go-live date: `____________`

---

## 1. Platform access ⏳ (start first — has approval lead time)

You only need **one** path per platform: **OAuth** (cleaner long-term, needs app
review) **or** **Manual token** (works immediately, good to start posting before
review clears).

### Facebook (Pages)
- ☐ Facebook **Page** to post to — Page name: `____________`  Page ID: `____________`
- **OAuth path:**
  - ☐ Meta app created → `META_APP_ID`: `____________`  `META_APP_SECRET`: `____________`
  - ☐ Business Verification submitted
  - ☐ App Review for `pages_manage_posts` (+ `pages_show_list`, `pages_read_engagement`) requested
- **Manual path (faster):**
  - ☐ Page **access token** obtained (a long-lived/Page token) → enter via *Add manually*

### Threads
- ☐ Threads **user ID**: `____________`
- **OAuth path:** ☐ uses the same Meta app; scopes `threads_basic`, `threads_content_publish` granted
- **Manual path:** ☐ Threads access token obtained → enter via *Add manually*

### LinkedIn
- ☐ Posting target: ☐ personal profile  ☐ company page
- ☐ **Author URN**: `urn:li:person:____` or `urn:li:organization:____`
- **OAuth path:**
  - ☐ LinkedIn app created → `LINKEDIN_CLIENT_ID`: `____________`  `LINKEDIN_CLIENT_SECRET`: `____________`
  - ☐ "Share on LinkedIn" / Community Management product approved (scope `w_member_social`)
- **Manual path:** ☐ access token (+ optional refresh token & expiry) → enter via *Add manually*

---

## 2. AI drafting (optional but recommended)

Provide **at least one** key (billed to the client's own account, so they control
cost & data). A provider with no key is simply hidden in the UI; with none, posts
can still be written manually.

- ☐ Anthropic (Claude) — `ANTHROPIC_API_KEY`: `____________`
- ☐ OpenAI (GPT) — `OPENAI_API_KEY`: `____________`
- ☐ Google (Gemini) — `GEMINI_API_KEY`: `____________`
- ☐ Preferred default model: `____________` (e.g. `claude-opus-4-8`)

---

## 3. Hosting & domain (Premium / done-for-you deploys)

Skip if the client self-hosts or runs locally.

- ☐ VPS provisioned (Python 3.12 + PostgreSQL) — host/IP: `____________`
- ☐ Domain for the dashboard: `https://____________`
- ☐ TLS certificate (e.g. certbot) — **required** for OAuth redirect URIs
- ☐ `APP_BASE_URL` set to the HTTPS domain (no trailing slash)
- ☐ OAuth redirect URIs registered in each platform app:
  `https://<domain>/oauth/facebook/callback`,
  `https://<domain>/oauth/linkedin/callback`,
  `https://<domain>/oauth/threads/callback`

### Media storage (for image/video posting)
- ☐ S3 (or S3-compatible) **bucket** — name: `____________`  region: `____________`
- ☐ Access keys: `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (or instance role)
- ☐ Bucket objects are **publicly readable** (platforms fetch media by URL) — or a
  CDN/public base URL: `____________`  (`S3_PUBLIC_BASE_URL`)
- ☐ *(optional)* S3-compatible endpoint (R2/MinIO/Spaces): `____________`
  > No bucket? The app falls back to local-disk storage served from the dashboard
  > host — fine for testing, but the host must be publicly reachable for posting.

---

## 4. App configuration

- ☐ Admin login email: `____________`  (`ADMIN_EMAIL`)
- ☐ Admin password set securely (`ADMIN_PASSWORD`) — change from default
- ☐ Display timezone: `____________`  (`DISPLAY_TIMEZONE`, e.g. `America/New_York`)
- ☐ `FERNET_KEY` generated (token encryption):
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- ☐ `SESSION_SECRET` set to a long random string

---

## 5. Content & brand inputs

- ☐ Brand voice / tone guidance (formal, casual, witty…): `____________`
- ☐ Topics, themes, or a content calendar to seed posts
- ☐ Posting cadence (e.g. 3×/week, weekdays 9am): `____________`
- ☐ Per-platform notes (hashtags, mentions, links, character-limit preferences)
- ☐ Approval workflow: who reviews/approves before scheduling? `____________`
- 🖼️ Media: images (carousels) and video are supported — collect any brand
  imagery/clips and confirm the S3 bucket above is set up.

---

## 6. Handover (end of project)

- ☐ Dashboard URL + admin credentials delivered
- ☐ At least one account connected & a test post published successfully
- ☐ Walkthrough / training done (per package)
- ☐ Source code, `.env` template, README, and deploy files handed over
- ☐ Support window & (optional) maintenance retainer agreed

---

*Minimum to go live:* one connected account per platform (token or OAuth), the
display timezone + admin login, and — if AI drafting is wanted — one AI key.
Everything in Section 1 should be requested on day one because of approval delays.
