from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, func, ForeignKey, Integer, DECIMAL
from datetime import datetime
from dotenv import load_dotenv
import os
from typing import AsyncGenerator
from decimal import Decimal

load_dotenv()
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('PSQL_USER')}:{os.getenv('PSQL_PASSWD')}@localhost:5430/{os.getenv('PSQL_DB')}"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30))
    telegram_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String(100))
    balance: Mapped[Decimal] = mapped_column(DECIMAL(precision=10, scale=2), default=Decimal('0.00'))
    locale: Mapped[str] = mapped_column(String(10),default='ru')
    referral_link: Mapped[str] = mapped_column(String(100),nullable=True)

class Sublink(Base, TimestampMixin):
    __tablename__ = "sublinks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    username: Mapped[str] = mapped_column(String(500))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    rate: Mapped[int] = mapped_column(Integer)

class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    platform: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column()

class ReferralLink(Base, TimestampMixin):
    __tablename__ = "referral_links" 
    
    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
