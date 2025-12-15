FROM pypy:slim-trixie

COPY . /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PATH="/root/.local/bin/:$PATH"
ENV UV_NO_DEV=1

WORKDIR /app

RUN uv sync --locked

CMD ["uv", "run",  "main.py"]
