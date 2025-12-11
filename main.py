import asyncio

from usecases.check_targets import CheckTargetsUseCase

if __name__ == '__main__':
    asyncio.run(CheckTargetsUseCase().execute())
