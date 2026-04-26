FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY . ./
RUN uv sync --no-dev

CMD ["uv", "run", "uvicorn", "--host", "0.0.0.0", "src.api.main:app", "--reload"]
