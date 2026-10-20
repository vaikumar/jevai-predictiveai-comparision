# Decision Lab — separate local services

## Start

From this directory run:

```sh
./run.sh
```

This starts three independent Uvicorn processes and checks their health. Ctrl+C stops them all. The launcher refuses occupied ports and stops the remaining children if one exits.

| Component | Local URL | Main endpoint |
|---|---|---|
| Dashboard and benchmark coordinator | http://127.0.0.1:8000 | POST /api/benchmark |
| Predictive AI service | http://127.0.0.1:8001 | POST /api/predict |
| JEV AI service | http://127.0.0.1:8002 | POST /api/jev |

Each service exposes `/health` and `/docs`. To launch separately, use three terminals:

```sh
./run.sh predictive
./run.sh jev
./run.sh dashboard
```

The launcher uses the existing `../../work/venv` environment or installs pinned dependencies in `.venv`. Python 3.13 was tested. `runtime.sh` supplies the bundled macOS OpenMP runtime for XGBoost.

## Endpoint configuration

Edit `service_urls.json`:

```json
{
  "dashboard": "http://127.0.0.1:8000",
  "predictive": "http://127.0.0.1:8001",
  "jev": "http://127.0.0.1:8002"
}
```

Restart all services and refresh the browser after edits. The launcher derives local ports from this file. The dashboard exposes these non-secret settings through GET /api/config. `static/api.js` loads them and calls the predictive and JEV services directly for single comparisons. The benchmark coordinator uses the same URLs through `service_clients.py`. CORS is restricted to the configured dashboard origin and its localhost alias. Current deployment supports loopback HTTP URLs only.

The provider endpoint and model are centralized in `settings.py`: https://api.typesafe.ai/v1/systemone and jev-latest. Do not put API keys in service_urls.json or JavaScript.

## File responsibilities

| File | Responsibility |
|---|---|
| schema.py | Strict login JSON contract; five required booleans and optional metadata strings |
| policy.py | Shared class labels, four-feature extraction, label rules and JEV instruction text |
| synthetic_data.py | Reproducible synthetic request generation |
| train_model.py | Offline XGBoost training, evaluation and artifact generation |
| train.sh | Standalone training command |
| predictor.py | Load saved model, extract features and execute inference |
| predictive_api.py | Predictive service endpoints and model startup/warmup |
| jev_client.py | Provider payload, authentication header, HTTP invocation, response validation and error mapping |
| jev_api.py | JEV service endpoints and in-memory credential verification/configuration |
| service_clients.py | HTTP calls from benchmark/dashboard coordinator to the backend services |
| benchmark.py | Fixed cohort execution, timings, accuracy, F1 and agreement calculations |
| dashboard_api.py | Serve UI, expose config, route benchmark jobs and optional comparison gateway |
| static/index.html | Dashboard markup |
| static/style.css | Dashboard appearance and responsive layout |
| static/app.js | UI event handling and rendering |
| static/api.js | Browser API invocation using configured service URLs |
| static/examples.json | Generated examples for the request selector |
| service_urls.json | Non-secret endpoint URLs for all local services |
| settings.py | Shared configuration loader and upstream JEV endpoint/model |
| service_security.py | Host/origin restrictions and CORS configuration |
| launch.py | Process supervisor, port checks, readiness checks and shutdown |
| runtime.sh | Shared Python environment setup |
| run.sh | Start all services or one selected service |
| test_app.py | Service, CORS, inference, gateway and mocked JEV tests |
| requirements.txt | Pinned Python dependencies |
| app.py / model.py | Compatibility imports/commands; no duplicate business logic |

## Training

```sh
./train.sh
```

Training is separate from inference startup. The predictive service fails with an actionable message if its model is absent; it never silently trains during startup. Restart the predictive process after retraining to load the new artifact. Running training rewrites generated artifacts.

Training uses 6,000 records (seed 42), test uses 1,200 (seed 99), and XGBoost uses 60 boosting rounds, depth 3 and learning rate 0.1. Dataset files are exported after generation; editing them does not change training because training currently consumes generated in-memory records.

## Assumed demo policy

1. Block when failure_ind AND credential_remed_manda are true.
2. Otherwise Challenge when either flag is true, or device_bounded OR device_linked is false.
3. Otherwise allow.

These are provisional assumptions, not validated login/fraud rules. Only those four booleans drive both models. remember_my_device is accepted but does not prove trust. The API accepts the original field names, including Channel, password_status_cdoe and browser_accet_lang. Optional metadata may be blank; dates, GPS and IP addresses are treated as text, not interpreted. Local results and exports contain submitted requests, but identifiers, IP and GPS are excluded from the upstream JEV payload.

With only 16 distinct boolean feature combinations, perfect holdout accuracy is expected for this deterministic task. Independent generated records still repeat those feature patterns. This is rule imitation, not evidence of fraud-detection generalization. No real access-control system is connected.

## JEV key

Only the JEV service loads TYPESAFE_API_KEY from its environment or accepts a key through the dashboard's Verify & connect dialog. The all-service launcher removes the credential from the other child processes' environments. The key is not persisted or returned to clients. UI-entered keys are cleared when the JEV service restarts.

Verify & connect sends one synthetic provider request and may use credits. An invalid candidate does not replace a prior key. A 401 means provider authentication was rejected; use the full current TypeSafe key from https://console.typesafe.ai. Provider request format follows https://docs.typesafe.ai/api. Live access remains unverified without a valid credential. No keys are stored in this repository.

## Benchmark metrics

POST /api/benchmark on port 8000 accepts `{"count":20,"include_jev":false}`; count supports 5–100. UI offers 5, 20, 50 and 100. Each row invokes both selected services concurrently through HTTP; rows are sequential. The fixed test set is regenerated with seed 99.

Model service latency excludes browser and local service-to-service transport; JEV's service latency includes upstream network and response validation. Total benchmark elapsed time includes coordinator HTTP overhead. No retries; the upstream HTTP client uses a 20-second timeout configuration. Accuracy/F1 and percentile latencies use successful results, with failures and skips counted separately. Exports also contain correct-per-attempt and whole-run completion rate (not sustained-load capacity). Agreement is not accuracy. P95 from small samples is exploratory. JSON exports preserve per-request evidence and model identifiers. UI results remain in browser memory until exported.

## Verification

Four grouped automated tests cover all 16 flag combinations, metadata invariance, validation, CORS and untrusted origins, missing keys, mocked JEV success and 401 verification, actual gateway URL selection, benchmark counting and unavailable service handling. Live checks verified all three health endpoints, a cross-service comparison and a 20-record benchmark. Browser checks verified direct cross-origin prediction and benchmark rendering. The standalone training command also completed successfully. No successful live JEV evaluation is claimed.

From this directory, run tests in the prepared environment:

```sh
. ./runtime.sh
"$PY" -m unittest test_app -v
```

Artifacts include model.json, metrics.json, synthetic-train.jsonl, synthetic-test.jsonl, sample-request.json and local-benchmark.json. This is a local single-user demonstration; production requires representative labeled outcomes, reviewed policies, authentication, experiment persistence and operational validation.
