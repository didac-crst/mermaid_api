# Mermaid Render API

FastAPI service that validates Mermaid syntax and renders diagrams to SVG/PNG/JPEG.

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

