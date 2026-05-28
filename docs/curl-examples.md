# Curl Examples

These examples embed the Mermaid text directly in the JSON payload.

They use Bash-style `$'...'` strings so `\n` works cleanly. For automation tests, prefer JSON payload files with `--data-binary @payload.json`.

## Error handling with curl

`POST /render` returns **either** a binary image **or** a JSON error. It never returns both in one response.

| HTTP status | `Content-Type` | Body |
|-------------|----------------|------|
| `200` | `image/svg+xml`, `image/png`, or `image/jpeg` | Diagram bytes |
| `400` | `application/json` | `{ "detail": { "error": { "code": "MERMAID_PARSE_ERROR", "message": "..." } } }` |
| `422` | `application/json` | Pydantic validation error (invalid `format`, `scale`, etc.) |
| `504` | `application/json` | `{ "detail": { "error": { "code": "MERMAID_RENDER_TIMEOUT", ... } } }` |

### `curl --output` does not mean success

`--output diagram.png` writes the response body to that path **even when the status is `400`**. A failed render can produce a small JSON file named `diagram.png`. Always check the HTTP status (or use `curl -f`) before treating the file as an image.

Verify a saved file when unsure:

```sh
file diagram.png
# PNG image data, ...        -> success
# JSON data                  -> error body saved under a .png name
```

### Success responses do not print `HTTP 200` by default

`curl -s` only prints the **body**. On success that body is binary image data, not JSON, so the terminal often looks empty. Errors look louder because the body is JSON text.

To see the status line or code on success:

```sh
curl -sS -o diagram.png -w "HTTP %{http_code}\n" ...
# or
curl -sS -D - -o diagram.png ...
```

### Option A: fail on HTTP errors (`curl -f`)

`-f` makes curl exit with a non-zero status on `4xx`/`5xx` and **does not** write `--output` on failure (the error body goes to stderr unless you redirect it).

```sh
curl -fS http://localhost:3000/render \
  -H "content-type: application/json" \
  -d '{"code":"flowchart TD\nA-->B","format":"png"}' \
  --output diagram.png

echo "Saved diagram.png ($(file -b diagram.png))"
```

On error, curl prints nothing useful to `diagram.png` and exits non-zero; handle that in your script:

```sh
if ! curl -fS http://localhost:3000/render \
  -H "content-type: application/json" \
  -d @bad-payload.json \
  --output diagram.png 2>render-error.json; then
  echo "Render failed:"
  cat render-error.json
  exit 1
fi
```

### Option B: capture the status code explicitly

Use a temp body file and branch on `%{http_code}`:

```sh
body="$(mktemp)"
http_code="$(curl -sS -o "$body" -w "%{http_code}" \
  http://localhost:3000/render \
  -H "content-type: application/json" \
  -d @payload.json)"

if [ "$http_code" = "200" ]; then
  mv "$body" diagram.png
  echo "OK: $(file -b diagram.png)"
else
  echo "HTTP $http_code"
  cat "$body"
  rm -f "$body"
  exit 1
fi
```

### Option C: validate first, then render

`POST /validate` always returns JSON. Use it when you want structured errors before requesting an image:

```sh
curl -s http://localhost:3000/validate \
  -H "content-type: application/json" \
  -d '{"code":"ishikawa-beta\n    Root cause\n    Category\n        Item"}' | jq .

# If "valid": true, call /render with the same code (using -f or status check above).
```

### Parse error JSON with `jq`

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d '{"code":"not valid mermaid","format":"png"}' \
| jq -r '.detail.error | "\(.code): \(.message)"'
```

The diagram examples below use `curl -s` for brevity. In scripts and CI, prefer **`curl -fS`** or **Option B** so errors are not saved as `.png` / `.svg` files.

## 1. Flowchart: Render Pipeline as SVG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "flowchart TD\\n    A[Client sends POST /render] --> B{Request valid?}\\n    B -- No --> B1[Return 422 validation error]\\n    B -- Yes --> C[Normalize render options]\\n    C --> D{Format requested}\\n    D -- svg --> E[Render Mermaid to SVG]\\n    D -- png/jpeg --> F[Render Mermaid to SVG first]\\n    E --> G{Mermaid parse OK?}\\n    F --> G\\n    G -- No --> H[Return 400 parse_error]\\n    G -- Yes --> I{Render timeout?}\\n    I -- Yes --> J[Return 504 render_timeout]\\n    I -- No --> K{Output format}\\n    K -- svg --> L[Return image/svg+xml]\\n    K -- png --> M[Rasterize SVG to PNG]\\n    K -- jpeg --> N[Rasterize SVG to JPEG]\\n    M --> O[Return image/png]\\n    N --> P[Return image/jpeg]\\n    subgraph Browser Lifecycle\\n        Q[FastAPI startup] --> R[Launch Playwright Chromium]\\n        R --> S[Reuse browser context]\\n        S --> T[FastAPI shutdown]\\n        T --> U[Close browser]\\n    end\\n    C -. uses .-> S",
    "format": "svg",
    "theme": "default",
    "transparent": true
  }' \
  --output render_pipeline.svg
```

## 2. Flowchart With Subgraphs as PNG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "flowchart LR\\n    subgraph Client[Client Layer]\\n        Browser[Browser]\\n        CLI[curl / CLI]\\n        Backend[Backend Service]\\n    end\\n\\n    subgraph CloudRun[Google Cloud Run]\\n        API[FastAPI App]\\n        Renderer[Mermaid Renderer]\\n        Chromium[Playwright Chromium]\\n        Vendor[Vendored Mermaid ESM]\\n    end\\n\\n    subgraph Observability[Observability]\\n        Logs[Structured Logs]\\n        Metrics[Latency Metrics]\\n        Alerts[Timeout Alerts]\\n    end\\n\\n    Browser -->|POST /render| API\\n    CLI -->|POST /validate| API\\n    Backend -->|Internal request| API\\n\\n    API --> Renderer\\n    Renderer --> Chromium\\n    Renderer --> Vendor\\n\\n    API --> Logs\\n    API --> Metrics\\n    Metrics --> Alerts\\n\\n    API -->|SVG / PNG / JPEG| Browser\\n    API -->|JSON validation result| CLI",
    "format": "png",
    "theme": "default",
    "width": 1400,
    "height": 900,
    "scale": 2,
    "background": "white"
  }' \
  --output deployment_architecture.png
```

## 3. ER Diagram as SVG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "erDiagram\\n    CLIENT ||--o{ RENDER_REQUEST : sends\\n    CLIENT ||--o{ VALIDATE_REQUEST : sends\\n\\n    RENDER_REQUEST ||--|| MERMAID_CODE : contains\\n    VALIDATE_REQUEST ||--|| MERMAID_CODE : contains\\n\\n    RENDER_REQUEST ||--|| RENDER_OPTIONS : uses\\n    RENDER_OPTIONS ||--|| OUTPUT_FORMAT : selects\\n    RENDER_OPTIONS ||--o| BACKGROUND : configures\\n\\n    RENDER_REQUEST ||--o| RENDER_RESULT : produces\\n    RENDER_REQUEST ||--o| RENDER_ERROR : may_produce\\n\\n    MERMAID_CODE {\\n        string code\\n        int size_bytes\\n        string diagram_type\\n    }\\n\\n    RENDER_OPTIONS {\\n        string format\\n        string theme\\n        int width\\n        int height\\n        float scale\\n        boolean transparent\\n        string background\\n    }\\n\\n    OUTPUT_FORMAT {\\n        string name\\n        string media_type\\n        boolean raster\\n    }\\n\\n    RENDER_RESULT {\\n        string content_type\\n        bytes body\\n        int duration_ms\\n    }\\n\\n    RENDER_ERROR {\\n        string error_code\\n        string message\\n        int status_code\\n    }\\n\\n    CLIENT {\\n        string user_agent\\n        string api_key_optional\\n    }",
    "format": "svg",
    "theme": "default",
    "transparent": true
  }' \
  --output api_domain_model.svg
```

## 4. Ishikawa / Fishbone as PNG

Requires Mermaid `11.15.0` (pinned in this repo). The diagram type is `ishikawa-beta`.

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "ishikawa-beta\\n    Late Mermaid Render Response\\n    People\\n        Unclear ownership\\n        No on-call rotation\\n        Limited Playwright expertise\\n    Process\\n        No E2E tests\\n        No performance budget\\n        Manual release validation\\n    Technology\\n        Cold Chromium startup\\n        Large Mermaid diagrams\\n        Insufficient timeout tuning\\n        Memory pressure\\n    Environment\\n        Cloud Run cold starts\\n        CPU throttling\\n        Container image too large\\n    Input\\n        Invalid Mermaid syntax\\n        Very large code payload\\n        Unsupported diagram features\\n    Measurement\\n        No render duration metric\\n        No diagram size histogram\\n        No timeout dashboard",
    "format": "png",
    "theme": "default",
    "width": 1600,
    "height": 1000,
    "scale": 2,
    "background": "white"
  }' \
  --output ishikawa_late_response.png
```

## 5. Sequence Diagram as SVG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "sequenceDiagram\\n    autonumber\\n\\n    participant Client\\n    participant API as FastAPI /render\\n    participant Renderer\\n    participant Browser as Playwright Chromium\\n    participant Mermaid\\n    participant Rasterizer\\n\\n    Client->>API: POST /render\\n    API->>Renderer: render(code, options)\\n\\n    Renderer->>Browser: open page\\n    Renderer->>Browser: inject Mermaid runtime\\n    Browser->>Mermaid: initialize(theme, securityLevel)\\n    Browser->>Mermaid: render(diagramId, code)\\n\\n    alt Parse error\\n        Mermaid-->>Browser: throws parse error\\n        Browser-->>Renderer: parse error details\\n        Renderer-->>API: RenderError(parse_error)\\n        API-->>Client: 400 JSON error\\n    else Timeout\\n        Browser--xRenderer: no response before deadline\\n        Renderer-->>API: RenderError(render_timeout)\\n        API-->>Client: 504 JSON error\\n    else SVG success\\n        Mermaid-->>Browser: SVG markup\\n        Browser-->>Renderer: SVG\\n\\n        alt format is svg\\n            Renderer-->>API: SVG bytes\\n            API-->>Client: 200 image/svg+xml\\n        else format is png or jpeg\\n            Renderer->>Rasterizer: rasterize(svg, width, height, scale)\\n            Rasterizer-->>Renderer: image bytes\\n            Renderer-->>API: image bytes\\n            API-->>Client: 200 image/png or image/jpeg\\n        end\\n    end",
    "format": "svg",
    "theme": "default",
    "transparent": true
  }' \
  --output render_sequence.svg
```

## 6. State Diagram as PNG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "stateDiagram-v2\\n    [*] --> Received\\n\\n    Received --> ValidatingRequest\\n    ValidatingRequest --> Rejected: schema invalid\\n    ValidatingRequest --> PreparingRenderer: schema valid\\n\\n    PreparingRenderer --> ParsingMermaid\\n    ParsingMermaid --> ParseFailed: syntax error\\n    ParsingMermaid --> Rendering: syntax ok\\n\\n    Rendering --> RenderTimedOut: timeout exceeded\\n    Rendering --> RenderedSVG: SVG generated\\n\\n    RenderedSVG --> ReturningSVG: format = svg\\n    RenderedSVG --> Rasterizing: format = png/jpeg\\n\\n    Rasterizing --> RasterFailed: browser/image error\\n    Rasterizing --> ReturningImage: raster ok\\n\\n    ReturningSVG --> Completed\\n    ReturningImage --> Completed\\n\\n    Rejected --> [*]\\n    ParseFailed --> [*]\\n    RenderTimedOut --> [*]\\n    RasterFailed --> [*]\\n    Completed --> [*]",
    "format": "png",
    "theme": "forest",
    "width": 1200,
    "height": 900,
    "scale": 2,
    "background": "white"
  }' \
  --output render_lifecycle.png
```

## 7. Class Diagram as SVG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "classDiagram\\n    class MermaidRenderRequest {\\n        +string code\\n        +string format\\n        +string theme\\n        +int width\\n        +int height\\n        +float scale\\n        +bool transparent\\n        +string background\\n    }\\n\\n    class MermaidRenderer {\\n        -Browser browser\\n        -Path mermaid_module_path\\n        +validate(code) ValidationResult\\n        +render(request) RenderResult\\n        -render_svg(code, options) string\\n        -rasterize(svg, format, options) bytes\\n    }\\n\\n    class RenderResult {\\n        +bytes body\\n        +string media_type\\n        +int duration_ms\\n    }\\n\\n    class ValidationResult {\\n        +bool valid\\n        +string error_message\\n    }\\n\\n    class RenderError {\\n        +string code\\n        +string message\\n        +int status_code\\n    }\\n\\n    class FastAPIApp {\\n        +GET health()\\n        +POST validate()\\n        +POST render()\\n    }\\n\\n    FastAPIApp --> MermaidRenderRequest\\n    FastAPIApp --> MermaidRenderer\\n    MermaidRenderer --> ValidationResult\\n    MermaidRenderer --> RenderResult\\n    MermaidRenderer --> RenderError",
    "format": "svg",
    "theme": "default",
    "transparent": true
  }' \
  --output renderer_class_diagram.svg
```

## 8. Mindmap as PNG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "mindmap\\n  root((Mermaid Render API Tests))\\n    Unit Tests\\n      Schema defaults\\n      Enum validation\\n      Size limits\\n      Background transparency logic\\n    Endpoint Tests\\n      Health\\n      Validate success\\n      Validate parse failure\\n      Render SVG success\\n      Render PNG success\\n      Render timeout\\n      Invalid payload\\n    Browser E2E Tests\\n      Real Mermaid parse\\n      Real SVG render\\n      Real PNG rasterization\\n      Theme handling\\n      Large diagram\\n    Non Functional\\n      Load test\\n      Cold start timing\\n      Memory usage\\n      Concurrent requests\\n      Timeout behavior",
    "format": "png",
    "theme": "default",
    "width": 1400,
    "height": 1000,
    "scale": 2,
    "background": "white"
  }' \
  --output test_strategy_mindmap.png
```

## 9. Gantt Diagram as SVG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "gantt\\n    title Mermaid Render API Roadmap\\n    dateFormat  YYYY-MM-DD\\n    axisFormat  %d %b\\n\\n    section MVP\\n    FastAPI endpoints           :done,    mvp1, 2026-05-01, 3d\\n    Pydantic schemas            :done,    mvp2, after mvp1, 2d\\n    Playwright renderer         :done,    mvp3, after mvp2, 4d\\n    Dockerfile                  :done,    mvp4, after mvp3, 2d\\n\\n    section Quality\\n    Unit tests                  :done,    q1, 2026-05-12, 2d\\n    Endpoint tests              :done,    q2, after q1, 2d\\n    E2E browser tests           :active,  q3, 2026-05-18, 4d\\n    Load tests                  :         q4, after q3, 3d\\n\\n    section Operations\\n    Structured logging          :         o1, 2026-05-24, 2d\\n    Metrics                     :         o2, after o1, 2d\\n    Cloud Run deployment        :         o3, after o2, 2d\\n    Alerting                    :         o4, after o3, 2d",
    "format": "svg",
    "theme": "default",
    "transparent": true
  }' \
  --output roadmap_gantt.svg
```

## 10. Git Graph as SVG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "gitGraph\\n    commit id: \\"init\\"\\n    branch feature/api\\n    checkout feature/api\\n    commit id: \\"health\\"\\n    commit id: \\"validate\\"\\n    commit id: \\"render\\"\\n\\n    checkout main\\n    merge feature/api\\n\\n    branch feature/docker\\n    checkout feature/docker\\n    commit id: \\"dockerfile\\"\\n    commit id: \\"install-mermaid\\"\\n\\n    checkout main\\n    merge feature/docker\\n\\n    branch feature/tests\\n    checkout feature/tests\\n    commit id: \\"schema-tests\\"\\n    commit id: \\"route-tests\\"\\n\\n    checkout main\\n    merge feature/tests\\n    commit id: \\"mvp-ready\\"",
    "format": "svg",
    "theme": "default",
    "transparent": true
  }' \
  --output git_graph.svg
```

## 11. Large Flowchart Stress Test as PNG

```sh
curl -s http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "flowchart TD\\n    N01[Step 01: Receive request] --> N02[Step 02: Validate JSON]\\n    N02 --> N03[Step 03: Validate schema]\\n    N03 --> N04[Step 04: Normalize options]\\n    N04 --> N05[Step 05: Check code size]\\n    N05 --> N06[Step 06: Create render job]\\n    N06 --> N07[Step 07: Acquire browser page]\\n    N07 --> N08[Step 08: Inject Mermaid module]\\n    N08 --> N09[Step 09: Initialize Mermaid]\\n    N09 --> N10[Step 10: Parse diagram]\\n    N10 --> N11[Step 11: Render SVG]\\n    N11 --> N12[Step 12: Validate SVG output]\\n    N12 --> N13[Step 13: Apply background]\\n    N13 --> N14[Step 14: Decide output format]\\n    N14 --> N15[Step 15: Return SVG or rasterize]\\n    N15 --> N16[Step 16: Rasterize PNG]\\n    N16 --> N17[Step 17: Rasterize JPEG]\\n    N17 --> N18[Step 18: Set content type]\\n    N18 --> N19[Step 19: Set cache headers]\\n    N19 --> N20[Step 20: Return response]\\n    N20 --> N21[Step 21: Record metrics]\\n    N21 --> N22[Step 22: Release page]\\n    N22 --> N23[Step 23: Complete request]\\n    N23 --> N24[Step 24: Await next request]",
    "format": "png",
    "theme": "default",
    "width": 1600,
    "height": 1200,
    "scale": 2,
    "background": "white"
  }' \
  --output large_flowchart.png
```

## 12. Invalid Mermaid Parse Error Test

This should return `400` JSON with `MERMAID_PARSE_ERROR`, not an image file.

```sh
curl -sS http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "flowchart TD\\n    A[Start --> B[Missing closing bracket]",
    "format": "svg",
    "theme": "default",
    "transparent": true
  }' \
| jq .
```

Expected shape:

```json
{
  "detail": {
    "error": {
      "code": "MERMAID_PARSE_ERROR",
      "message": "..."
    }
  }
}
```

Do **not** pipe this directly to `--output diagram.svg` without checking status; curl would save the JSON into a file named like an image.

## 13. Wrong Diagram Type (typo) — JSON saved as `.png`

A common mistake is a typo in the first line (e.g. `ishiFLOWCHART-beta` instead of `ishikawa-beta`). The API correctly returns `400` JSON, but `curl --output file.png` still writes that JSON to disk:

```sh
# Wrong diagram header on purpose
curl -sS -o ishikawa_late_response2.png -w "HTTP %{http_code}\n" \
  http://localhost:3000/render \
  -H "content-type: application/json" \
  -d $'{
    "code": "ishiFLOWCHART-beta\\n    Late Mermaid Render Response\\n    People\\n        Unclear ownership",
    "format": "png"
  }'

file ishikawa_late_response2.png
# JSON data   <- not a PNG; fix the code string and use curl -f or check HTTP status
```

Correct header for the Ishikawa example: `ishikawa-beta` (see section 4).

## Payload File Pattern

Inline JSON is useful for manual smoke testing, but payload files are easier to maintain for automation:

```sh
curl -fS http://localhost:3000/render \
  -H "content-type: application/json" \
  --data-binary @payload.json \
  --output diagram.svg
```

If the render fails, `curl -f` exits non-zero and does not leave a fake `diagram.svg` containing JSON.
