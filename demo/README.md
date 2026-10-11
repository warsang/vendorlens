# VendorLens demo page (jev-web on-device verdict layer)

A static page. Paste a vendor's homepage text, hit **Assess**, and a typed-decision
model (`jev-web`, Bekko 17m, about 29 MB) scores scam risk **entirely in the
browser**. No text leaves the device. This is the client-side verdict layer of
VendorLens, complementing the server-side OSINT agent.

`jev-web` is **vendored** under `demo/jev-web/` (MIT, extracted from the
`jev-web-0.7.2.tgz` tarball in `demo/vendor/`), so there is no build step and no
`node_modules` needed to run or deploy. `@huggingface/transformers` and
`onnxruntime-web` load from the jsDelivr CDN through the import map in
`index.html`; the Bekko model downloads from HuggingFace on first Assess (about
29 MB, browser-cached afterwards). After weights load, the decision itself makes
zero network requests.

## Run locally

```bash
cd demo
python -m http.server 8000     # or: npx serve .
# open http://localhost:8000
```

## Deploy for free (static hosting)

The folder is plain static files, so any free host works. Point each host at
this `demo/` folder as the site root / publish directory (it holds `index.html`
plus `jev-web/`).

**Cloudflare Pages (recommended, instant `*.pages.dev` URL):**

```bash
npm i -g wrangler
wrangler login                            # one-time, opens your browser
wrangler pages deploy demo --project-name vendorlens-demo
# -> https://vendorlens-demo.pages.dev
```

Or, no CLI: Cloudflare dashboard -> Workers & Pages -> Create -> Pages ->
Upload assets -> drag this `demo/` folder in. Or connect the repo via Pages ->
Create -> Connect to Git -> build command (none) -> build output directory
`demo`.

**Vercel:**

```bash
cd demo && npx vercel --prod              # then re-run for updates
```

**Netlify:**

```bash
npx netlify login                         # one-time
npx netlify deploy --dir=demo --prod
```

**GitHub Pages:** this host has historically served `.mjs` with a non-JS MIME
type, which can break ES modules. If you still use it, deploy `demo/` and keep
the `.nojekyll` file (it disables Jekyll). Cloudflare, Vercel and Netlify serve
the module build reliably and are preferred.

## What is NOT hostable here

The Python OSINT agent (`python -m vendorlens <domain>`) makes raw DNS
(UDP/53), WHOIS (TCP/43) and TLS (TCP/443) calls that edge and serverless
tiers forbid, so it runs locally and is captured in the demo video. This page
is the public "demo link" for the submission; the agent brief and trace run on
your machine.
