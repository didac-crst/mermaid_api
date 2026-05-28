# Mermaid Render API

FastAPI service that validates Mermaid syntax and renders diagrams to SVG/PNG/JPEG.

## Current State

The MVP implementation is in place and running with:

- FastAPI app with lifecycle-managed Playwright browser instance.
- Implemented endpoints: `GET /health`, `POST /validate`, `POST /render`.
- Pydantic request validation for format/theme/size/scale limits and code size cap.
- Mermaid render pipeline using `vendor/mermaid/dist/mermaid.min.js` injected into Playwright Chromium.
- Error mapping for parse failures, Mermaid error-diagram SVG detection, and render timeout responses.
- Dockerfile and Mermaid install script (`scripts/install_mermaid.sh`) with pinned Mermaid version support.

Current automated test status:

- `19` tests passing (`16` unit/route + `3` browser e2e).
- Unit coverage for schema defaults/constraints and background/transparency logic.
- Endpoint-level tests for success/error responses on health, validate, and render routes.

Notes:

- Route tests stub the renderer for deterministic API checks; browser e2e tests cover real Mermaid render/parse in `tests/test_render_e2e.py`.

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

Browser-backed tests (require `./scripts/install_mermaid.sh` and `playwright install chromium`):

```sh
pytest -m e2e
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

### Error handling

`POST /render` returns an **image on `200`** and **JSON on `4xx`/`504`**. `curl --output diagram.png` writes whatever body came back, including JSON errors, so a failed request can create a `.png` file that is not an image.

In scripts, use `curl -fS` (fail on HTTP errors) or check `%{http_code}` before treating the output file as a diagram. Plain `curl -s` does not print `HTTP 200` on success (only the binary image body); use `-w "%{http_code}"` or `-D -` to see the status. See [Error handling with curl](docs/curl-examples.md#error-handling-with-curl) for full examples, including `jq` and validate-then-render flows.

Validate:

```sh
curl -s http://localhost:3000/validate \
  -H "content-type: application/json" \
  -d '{"code":"flowchart TD\nA-->B"}'
```

Render PNG:

```sh
curl -fS http://localhost:3000/render \
  -H "content-type: application/json" \
  -d '{"code":"flowchart TD\nA-->B","format":"png","background":"white"}' \
  --output diagram.png
```

Render SVG:

```sh
curl -fS http://localhost:3000/render \
  -H "content-type: application/json" \
  -d '{"code":"flowchart TD\nA-->B","format":"svg","transparent":true}' \
  --output diagram.svg
```
