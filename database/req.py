from sqlalchemy import select, delete, update
from datetime import datetime
from typing import Optional, List
from database.db import User, Sublink ,get_session



async def create_user(username: str, telegram_id: int, name: str) -> User:
    async with get_session() as session:  # type: ignore
        user = User(username=username, telegram_id=telegram_id, name=name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def get_user_by_id(user_id: int) -> Optional[User]:
    async with get_session() as session:  # type: ignore
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()

async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    async with get_session() as session:  # type: ignore
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalars().first()

async def get_all_users() -> List[User]:
    async with get_session() as session:  # type: ignore
        stmt = select(User)
        result = await session.execute(stmt)
        return result.scalars().all()

async def update_user(user_id: int, **kwargs) -> Optional[User]:
    async with get_session() as session: 
        stmt = update(User).where(User.id == user_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
        return await get_user_by_id(user_id)

async def delete_user(user_id: int) -> bool:
    async with get_session() as session: 
        stmt = delete(User).where(User.id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0 


async def create_sublink(link: str, expires_at: datetime, username: str, user_id: int, rate: int) -> Sublink:
    async with get_session() as session:
        sublink = Sublink(link=link, expires_at=expires_at, username=username, user_id=user_id, rate=rate)
        session.add(sublink)
        await session.commit()
        await session.refresh(sublink)
        return sublink

async def get_sublink_by_id(sublink_id: int) -> Optional[Sublink]:
    async with get_session() as session: 
        stmt = select(Sublink).where(Sublink.id == sublink_id)
        result = await session.execute(stmt)
        return result.scalars().first()

async def get_sublink_by_user_id(user_id: int) -> List[Sublink]:
    async with get_session() as session:  
        stmt = select(Sublink).where(Sublink.user_id == user_id,)
        result = await session.execute(stmt)
        return result.scalars().all()

async def update_sublink(sublink_id: int, **kwargs) -> Optional[Sublink]:
    async with get_session() as session: 
        stmt = update(Sublink).where(Sublink.id == sublink_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()
        return await get_sublink_by_id(sublink_id)

async def delete_sublink(sublink_id: int) -> bool:
    async with get_session() as session:  
        stmt = delete(Sublink).where(Sublink.id == sublink_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0  