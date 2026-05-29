FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY pyproject.toml package.json /app/
RUN pip install --no-cache-dir -e "."
RUN playwright install --with-deps chromium

COPY . /app
RUN ./scripts/install_mermaid.sh

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app /ms-playwright

USER app

ENV PORT=3000
EXPOSE 3000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
