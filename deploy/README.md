# Deploy the live VendorLens endpoint (AWS Lambda)

The public demo page works with **zero backend** (the "Load example" button
renders a committed brief). This endpoint is only needed if you want the live
"Investigate" path: a domain/company name goes in, a fresh investigation runs,
and the page renders the verdict + the on-device model scores the homepage text.

Everything below runs against **your** AWS account. Authenticate first with
`aws login` (device flow) in this repo's directory, then run the steps in order.
The agent could not run these because the AWS session was expired.

## 1. Build the deployment zip

```bash
python deploy/build_lambda_zip.py        # -> deploy/vendorlens-lambda.zip (~32 MB)
```

It bundles the `vendorlens` package and only the runtime deps the handler
imports (`httpx`, `openai`, `dnspython`, `trafilatura`); `neatlogs` is optional
and degrades to a no-op if absent.

## 2. Create the function

```bash
ROLE_ARN=arn:aws:iam::<account>:role/<lambda-basic-execution-role>   # create if needed
PUBLIC_TOKEN=$(openssl rand -hex 16)                                  # a public client token, not auth

aws lambda create-function \
  --function-name vendorlens \
  --runtime python3.12 \
  --handler vendorlens.aws_lambda.lambda_handler \
  --role "$ROLE_ARN" \
  --zip-file fileb://deploy/vendorlens-lambda.zip \
  --timeout 60 --memory-size 512 \
  --environment "Variables={ALLOWED_ORIGIN=https://vendorlens-demo.pages.dev,VENDORLENS_API_KEY=$PUBLIC_TOKEN}"

# Cap blast radius / spend:
aws lambda put-function-concurrency \
  --function-name vendorlens --reserved-concurrent-executions 2
```

Optional env for live LLM + enrichment (leave unset to stay keyless/demo):
`NEATLOGS_API_KEY`, `CRUSTDATA_API_KEY`, `LITELLM_API_BASE`, `LITELLM_API_KEY`,
`LITELLM_MODEL`.

## 3. Put it behind an HTTPS API with throttling

```bash
# HTTP API in front of the function
aws apigatewayv2 create-api --name vendorlens-api --protocol-type HTTP \
  --target "arn:aws:lambda:<region>:<account>:function:vendorlens"

# Per-route throttle (a global ceiling; add WAF for true per-IP limits)
aws apigatewayv2 update-stage --api-id <API_ID> --stage-name '$default' \
  --default-route-settings ThrottlingRateLimit=5,ThrottlingBurstLimit=10
```

For genuine **per-IP** rate limiting, attach an AWS WAF rate-based rule to the
stage (`aws wafv2 create-web-acl` with a `RateBasedStatement`, e.g. 100 req / 5
min per IP). Reserved concurrency (step 2) already hard-caps runaway spend.

## 4. A hard spend ceiling

```bash
aws budgets create-budget --account-id <account> \
  --budget '{"BudgetName":"vendorlens-monthly","BudgetLimit":{"Amount":"5","Unit":"USD"},"TimeUnit":"MONTHLY","BudgetType":"COST"}' \
  --notifications-with-subscribers '[{"Notification":{"NotificationType":"ACTUAL","ComparisonOperator":"GREATER_THAN","Threshold":80,"ThresholdType":"PERCENTAGE"},"Subscribers":[{"SubscriptionType":"EMAIL","Address":"<you@example.com>"}]}]'
```

## 5. Point the page at it (optional backend build)

```bash
python demo/build.py --out dist \
  --api "https://<API_ID>.execute-api.<region>.amazonaws.com/<stage>" \
  --token "$PUBLIC_TOKEN"
# then deploy dist/ to Cloudflare Pages (wrangler pages deploy dist)
```

The `x-api-key` header is a **public client token** for rate/billing
attribution, NOT authentication: the real protections are the route throttle,
reserved concurrency, the pinned `ALLOWED_ORIGIN`, and the budget alarm. Never
commit the token; the committed `demo/index.html` keeps placeholders and is the
no-backend build.

## Verify

```bash
curl "https://<API_ID>.execute-api.<region>.amazonaws.com/$default?q=stripe.com&mode=nollm" \
  -H "x-api-key: $PUBLIC_TOKEN"
# -> {"ok": true, "verdict": {"band": "LOW", ...}}
```

Then load the deployed page from a phone on cellular and run one live
investigation end to end.
