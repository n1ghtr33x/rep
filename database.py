import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, select

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)

class Database:
    def __init__(self, db_url="sqlite+aiosqlite:///database.db"):
        self.engine = create_async_engine(db_url, echo=True)
        self.AsyncSessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def add_user(self, name: str, password: str, id: int):
        async with self.AsyncSessionLocal() as session:
            query = select(User).where(User.name == name)
            result = await session.execute(query)
            existing_user = result.scalars().first()

            if existing_user:
                return "user exists"

            new_user = User(name=name, password=password, id=id)
            session.add(new_user)
            await session.commit()
            return "user added"

    async def get_user(self, id: int):
        async with self.AsyncSessionLocal() as session:
            query = select(User).where(User.id == id)
            result = await session.execute(query)
            return result.scalars().first()
