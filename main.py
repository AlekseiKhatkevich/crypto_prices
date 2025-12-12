#!/usr/bin/env -S uv run --script
import anyio

from usecases.check_targets import CheckTargetsUseCase

if __name__ == '__main__':
    anyio.run(CheckTargetsUseCase().execute)
