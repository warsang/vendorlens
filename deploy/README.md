# Deploy the live VendorLens endpoint (AWS Lambda)

The public demo page at `https://vendorlens-demo.pages.dev` is **live-only**:
**Investigate** invokes this endpoint (a domain/company name goes in, a fresh
investigation runs, and the page renders the verdict). There is no canned
fallback in the page or in this deployment.

## Live resources (deployed)

| Resource | Value |
|---|---|
| Function | `vendorlens-agent` (python3.12, handler `vendorlens.aws_lambda.lambda_handler`, 300s, 1024 MB) |
| Execution role | `vendorlens-lambda-role` (AWSLambdaBasicExecutionRole) |
| API | `vendorlens-api` (HTTP API `gxqk0fcwne`), `$default` stage, Lambda proxy |
| Endpoint | `https://gxqk0fcwne.execute-api.us-east-1.amazonaws.com` |
| Hardening | reserved concurrency **2**, route throttle **5/s burst 10**, budget `vendorlens-monthly` ($10/mo) |
| Client token | env `VENDORLENS_API_KEY` on the function; `ALLOWED_ORIGIN=https://vendorlens-demo.pages.dev` |

Live keys (`LITELLM_*`, `CRUSTDATA_API_KEY`, `NEATLOGS_API_KEY`) are set as
Lambda env vars, never in the repo.

## Rebuild + deploy a code change

```bash
python deploy/build_lambda_zip.py          # -> deploy/vendorlens-lambda.zip (~40 MB)
aws lambda update-function-code \
  --function-name vendorlens-agent \
  --zip-file fileb://deploy/vendorlens-lambda.zip
aws lambda wait function-updated --function-name vendorlens-agent
```

`build_lambda_zip.py` installs **manylinux** wheels (`pip --platform
manylinux* --only-binary=:all:`) so native modules like `pydantic_core` run on
Lambda's Linux; it keeps package metadata (some imports read their version)
and drops only tests/stubs/docs.

## Verify

```bash
curl "https://gxqk0fcwne.execute-api.us-east-1.amazonaws.com?q=acme-cloud-services.example&mode=demo" \
  -H "x-api-key: $VENDORLENS_API_KEY"     # -> CRITICAL 100/100
curl "https://gxqk0fcwne.execute-api.us-east-1.amazonaws.com?q=stripe.com&mode=nollm" \
  -H "x-api-key: $VENDORLENS_API_KEY"     # -> LOW (live tools)
```

## Build + deploy the demo page

The committed `demo/index.html` keeps the `__AGENT_API__`/`__AGENT_TOKEN__`
placeholders; the build must substitute the real endpoint and public token
(it fails if either is missing). `demo/build.py` reads the gitignored
`deploy/.deploy.local` automatically, or take explicit flags:

```bash
python demo/build.py --out dist \
  --api "https://gxqk0fcwne.execute-api.us-east-1.amazonaws.com" \
  --token "$VENDORLENS_API_KEY"
wrangler pages deploy dist --project-name vendorlens-demo
```

## Remaining hardening (needs your input)

- **Budget notification:** attach an email to `vendorlens-monthly`
  (`aws budgets create-notification`) or in the console (Budgets -> the budget
  -> Add notification). No email is exposed via the API, so this needs you.
- **Per-IP rate limiting:** route throttling is a global ceiling. For true
  per-IP limits, attach an AWS WAF rate-based rule to the stage
  (`aws wafv2 create-web-acl` with a RateBasedStatement, then
  `associate-web-acl` on the stage ARN).
- **Root account:** the CLI session used `arn:aws:iam::<account>:root`.
  Prefer a scoped IAM user or role with permission only on this function for
  day-to-day deploys.

The `x-api-key` header is a **public client token** for rate/billing
attribution, NOT authentication: the real protections are the throttle,
reserved concurrency, the pinned `ALLOWED_ORIGIN`, and the budget ceiling.
Never commit the token; only the built `dist/` page contains it.
