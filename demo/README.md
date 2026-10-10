# VendorLens demo page (jev-web client-side verdict layer)

A static page: paste vendor homepage text, hit **Assess**, and a typed-decision
model (`jev-web`, Bekko 17m, ~29 MB) scores scam risk **entirely in the
browser**. No page text leaves the device — this is the private on-device
scoring layer of VendorLens, complementing the server-side OSINT agent.

## Run it

```bash
cd demo
npm install /home/hatch/workspace/jev-web/jev-web-0.7.2.tgz
npx serve .   # or: python3 -m http.server 8000
# open http://localhost:3000 (or :8000)
```

The page loads `@huggingface/transformers` and `onnxruntime-web` from CDN via
an import map; `jev-web` itself comes from the local tarball installed above.
First visit downloads the ~29 MB Bekko weights (browser-cached afterwards);
every decision after that makes zero network requests.

If the model fails to load (old browser, no WebAssembly), the page shows a
clear error message instead of hanging.
