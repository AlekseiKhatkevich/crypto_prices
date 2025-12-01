from contextlib import aclosing, asynccontextmanager
from typing import AsyncGenerator

import pydantic_core
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    _sessionmaker_kwargs = dict(
        expire_on_commit=False,
        join_transaction_mode='create_savepoint',
    )
    def __init__(self, connection: AsyncConnection | None = None, **kwargs) -> None:
        self._kwargs = kwargs
        self.connection = connection
        self._maker: async_sessionmaker | None = None

    def __new__(cls, **kwargs) -> 'Database':
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        # noinspection PyUnresolvedReferences
        return cls.instance

    @property
    def engine(self) -> AsyncEngine:
        engine = create_async_engine(
            **dict(
                url=settings.POSTGRES_DSN.unicode_string(),
                execution_options={},
                insertmanyvalues_page_size=2000,
                json_deserializer=pydantic_core.from_json,
                json_serializer=pydantic_core.to_json,
                echo=True,
                max_overflow=15,
                pool_pre_ping=True,
                pool_timeout=5,
                pool_size=5,
                connect_args={
                    'prepared_statement_name_func': lambda: f'__asyncpg_{ulid.ULID()}__',
                    'autocommit': False,
                },
            ) | self._kwargs,
        )
        return engine

    @property
    def async_sessionmaker(self) -> async_sessionmaker:
        if self._maker is None:
            self._maker = async_sessionmaker(self.engine, **self._sessionmaker_kwargs)
        if self.connection is not None:
            self._maker.configure(bind=self.connection)
        return self._maker

    @property
    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession]:
        async with aclosing(self.async_sessionmaker()) as async_session:
                yield async_session

    async def check_health(self) -> bool:
        try:
            async with self.async_session as session:
                await session.execute(text('SELECT 1'))
            return True
        except (SQLAlchemyError, OSError) as e:
            print(f'Database health check failed: {e}')
            return False

db = Database()
