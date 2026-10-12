# VendorLens demo page (live agent + on-device verdict layer)

A static page. Enter a company name or domain, hit **Investigate**, and the page
invokes the deployed VendorLens agent (AWS Lambda behind an HTTP API). The agent
runs a fresh OSINT investigation across live sources and returns a cited risk
verdict; the homepage text it returns is then scored on-device by a typed-decision
model (`jev-web`, Bekko 17m, about 29 MB) **entirely in the browser** — that text
never leaves the device.

`jev-web` is **vendored** under `demo/jeveb/` (MIT, extracted from the
`jev-web-0.7.2.tgz` tarball in `demo/vendor/`), so there is no build step and no
`node_modules` needed to run or deploy. `@huggingface/transformers` and
`onnxruntime-web` load from the jsDelivr CDN through the import map in
`index.html`; the Bekko model downloads from HuggingFace on page open (about
29 MB, preloaded on mount with a visible progress bar, browser-cached
afterwards). After weights load, the on-device scoring makes zero network
requests.

The committed `index.html` keeps the `__AGENT_API__`/`__AGENT_TOKEN__`
placeholders. `demo/build.py` replaces them with the deployed gateway URL and
the public client token and **fails if either is missing or any placeholder is
left**. There is no canned/no-backend fallback: an unbuilt page reports the
missing endpoint instead of replaying a captured run.

## Build

Values come from `--api`/`--token`, the `AGENT_API`/`AGENT_TOKEN` env vars, or
the gitignored `deploy/.deploy.local` (`ENDPOINT=` / `PUBLIC_TOKEN=`):

```bash
python demo/build.py --out dist
# or explicitly:
python demo/build.py --out dist \
  --api "https://gxqk0fcwne.execute-api.us-east-1.amazonaws.com" \
  --token "<public client token>"
```

## Run locally

```bash
python demo/build.py --out dist
python -m http.server -d dist 8000     # or: npx serve dist
# open http://localhost:8000
```

For local development the agent call is cross-origin, and the endpoint pins
`ALLOWED_ORIGIN` to `https://vendorlens-demo.pages.dev`; a localhost page is
rejected (401) until the Lambda's `ALLOWED_ORIGIN` is changed to match, then
changed back for the public deploy.

## Deploy for free (static hosting)

The built `dist/` folder is plain static files, so any free host works. Point
each host at `dist/` as the site root / publish directory (it holds
`index.html` plus the vendored assets).

**Cloudflare Pages (recommended, instant `*.pages.dev` URL):**

```bash
npm i -g wrangler
wrangler login                            # one-time, opens your browser
python demo/build.py --out dist
wrangler pages deploy dist --project-name vendorlens-demo
# -> https://vendorlens-demo.pages.dev
```

Or, no CLI: Cloudflare dashboard -> Workers & Pages -> Create -> Pages ->
Upload assets -> drag the built `dist/` folder in.

**Vercel:**

```bash
python demo/build.py --out dist && npx vercel --prod dist
```

**Netlify:**

```bash
npx netlify login                         # one-time
python demo/build.py --out dist && npx netlify deploy --dir=dist --prod
```

**GitHub Pages:** this host has historically served `.mjs` with a non-JS MIME
type, which can break ES modules. If you still use it, deploy the built `dist/`
and keep the `.nojekyll` file (it disables Jekyll). Cloudflare, Vercel and
Netlify serve the module build reliably and are preferred.

## What runs where

- **In the browser:** the on-device verdict model (`jev-web`/Bekko), which
  scores the homepage text the agent returned.
- **On AWS Lambda** (`vendorlens-agent`, setup and re-deploy in
  `deploy/README.md`): the OSINT agent and its tools. The `x-api-key` header is
  a **public client token** for rate/billing attribution, not authentication;
  the endpoint's real protection is request throttling, reserved concurrency,
  a spend budget, and the pinned `ALLOWED_ORIGIN`.
