FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl bzip2 ca-certificates \
 && mkdir -p /app \
 && curl -fsSL https://sourceforge.net/projects/geographiclib/files/geoids-distrib/egm2008-5.tar.bz2/download \
    | tar -xj -C /app \
 && apt-get purge -y curl bzip2 && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . ./
RUN uv sync --no-dev

CMD ["uv", "run", "service"]