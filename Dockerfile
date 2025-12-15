#https://docs.astral.sh/uv/guides/integration/docker/

FROM pypy:slim-trixie

COPY . /app

COPY --from=ghcr.io/astral-sh/uv:0.9.17 /uv /uvx /bin/

ENV PATH="/root/.local/bin/:$PATH"
ENV UV_NO_DEV=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv  \
    uv sync --locked

CMD ["uv", "run",  "main.py"]

# Запуск раз в 5 минут