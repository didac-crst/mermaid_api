# Mermaid Render API

FastAPI service that validates Mermaid syntax and renders diagrams to SVG/PNG/JPEG.

## Current State

The MVP implementation is in place and running with:

- FastAPI app with lifecycle-managed Playwright browser instance.
- Implemented endpoints: `GET /health`, `POST /validate`, `POST /render`.
- Pydantic request validation for format/theme/size/scale limits and code size cap.
- Mermaid render pipeline using the vendored Mermaid ESM module under `vendor/mermaid/dist`.
- Error mapping for parse failures and render timeout responses.
- Dockerfile and Mermaid install script (`scripts/install_mermaid.sh`) with pinned Mermaid version support.

Current automated test status:

- `13` tests passing.
- Unit coverage for schema defaults/constraints and background/transparency logic.
- Endpoint-level tests for success/error responses on health, validate, and render routes.

Notes:

- Tests currently stub the renderer at route-test level to keep API behavior checks deterministic.
- Full browser rendering behavior is implemented in `src/render/mermaid_renderer.py`; adding dedicated end-to-end Playwright-backed tests is the next recommended step.

## API Endpoints

- `GET /health`
- `POST /validate`
- `POST /render`

## Requirements

- Python 3.12+
- Node.js + npm (for Mermaid install script)
- Chromium dependencies (for Playwright)

## Local Setup

1. Install Python dependencies:

```sh
pip install -e ".[dev]"
```

2. Install Playwright browser:

```sh
playwright install --with-deps chromium
```

3. Install pinned Mermaid runtime:

```sh
./scripts/install_mermaid.sh
```

4. Start API:

```sh
npm run dev
```

The API listens on `http://localhost:3000`.

## Run Tests

```sh
npm test
```

## Docker

Rebuild the image after changing `MERMAID_VERSION` or running `scripts/install_mermaid.sh`; the container includes its own copy of `vendor/mermaid/dist`.

Build:

```sh
docker build -t mermaid-render-api .
```

Run:

```sh
docker run --rm -p 3000:3000 mermaid-render-api
```

## Cloud Run Deploy

```sh
gcloud builds submit --tag gcr.io/PROJECT_ID/mermaid-render-api
gcloud run deploy mermaid-render-api \
  --image gcr.io/PROJECT_ID/mermaid-render-api \
  --platform managed \
  --region REGION \
  --allow-unauthenticated
```

Use `--no-allow-unauthenticated` if you want IAM-protected invocations.

## Curl Examples

For a larger set of smoke-test examples across Mermaid diagram types, see
[docs/curl-examples.md](docs/curl-examples.md).

Validate:

```sh
curl -s http://localhost:3000/validate \
  -H "content-type: application/json" \
  -d '{"code":"flowchart TD\nA-->B"}'
```

Render PNG:

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d '{"code":"flowchart TD\nA-->B","format":"png","background":"white"}' \
  --output diagram.png
```

Render SVG:

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d '{"code":"flowchart TD\nA-->B","format":"svg","transparent":true}' \
  --output diagram.svg
```
