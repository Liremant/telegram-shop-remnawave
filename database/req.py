from sqlalchemy import select, update
from datetime import datetime
from typing import Optional, List
from database.db import User, Sublink, Invoice, ReferralLink, get_session


class BaseReqests:
    @staticmethod
    async def get_user_by_id(user_id: int) -> Optional[User]:
        async with get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
        async with get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            return result.scalars().first()


class UserRequests(BaseReqests):
    @staticmethod
    async def create_user(
        username: str, telegram_id: int, name: str, locale: str
    ) -> bool:
        async with get_session() as session:
            existing = await UserRequests.get_user_by_telegram_id(telegram_id)
            if existing:
                return False

            user = User(
                username=username, telegram_id=telegram_id, name=name, locale=locale
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    @staticmethod
    async def update_user(user_id: int, **kwargs) -> Optional[User]:
        async with get_session() as session:
            stmt = update(User).where(User.id == user_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()
            return await UserRequests.get_user_by_id(user_id)


class SublinkRequests(BaseReqests):
    @staticmethod
    async def create_sublink(
        link: str, expires_at: datetime, username: str, user_id: int, limit_gb, status
    ) -> Sublink:
        async with get_session() as session:
            sublink = Sublink(
                link=link,
                expires_at=expires_at,
                username=username,
                user_id=user_id,
                limit_gb=limit_gb,
                status=status,
            )
            session.add(sublink)
            await session.commit()
            await session.refresh(sublink)
            return sublink

    @staticmethod
    async def get_sublink_by_id(sublink_id: int) -> Optional[Sublink]:
        async with get_session() as session:
            stmt = select(Sublink).where(Sublink.id == sublink_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_sublink_by_user_id(user_id: int) -> List[Sublink]:
        async with get_session() as session:
            stmt = select(Sublink).where(Sublink.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def update_sublink(sublink_id: int, **kwargs) -> Optional[Sublink]:
        async with get_session() as session:
            stmt = update(Sublink).where(Sublink.id == sublink_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()
            return await SublinkRequests.get_sublink_by_id(sublink_id)

    @staticmethod
    async def get_sublink_by_link(link: int) -> Optional[Sublink]:
        async with get_session() as session:
            stmt = select(Sublink).where(Sublink.link == link)
            result = await session.execute(stmt)
            return result.scalars().first()


class InvoiceRequests(BaseReqests):
    @staticmethod
    async def create_invoice(
        status: str, user_id: int, platform: str, amount
    ) -> Invoice:
        async with get_session() as session:
            invoice = Invoice(
                status=status, user_id=user_id, platform=platform, amount=amount
            )
            session.add(invoice)
            await session.commit()
            await session.refresh(invoice)
            return invoice

    @staticmethod
    async def get_invoice_by_id(invoice_id: int) -> Optional[Invoice]:
        async with get_session() as session:
            stmt = select(Invoice).where(Invoice.id == invoice_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_invoices_by_user_id(user_id: int) -> List[Invoice]:
        async with get_session() as session:
            stmt = select(Invoice).where(Invoice.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def update_invoice(invoice_id: int, **kwargs) -> Optional[Invoice]:
        async with get_session() as session:
            stmt = update(Invoice).where(Invoice.id == invoice_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()
            return await InvoiceRequests.get_invoice_by_id(invoice_id)


class ReferralLinkRequests(BaseReqests):
    @staticmethod
    async def create_referral(
        owner_id: int,
        user_id: int,
        user_tgid,
        user_full_name,
    ) -> ReferralLink:
        async with get_session() as session:
            referral = ReferralLink(
                owner_id=owner_id,
                user_id=user_id,
                user_tgid=user_tgid,
                user_full_name=user_full_name,
            )
            session.add(referral)
            await session.commit()
            await session.refresh(referral)
            return referral

    @staticmethod
    async def get_referral_link_by_id(referral_id: int) -> Optional[ReferralLink]:
        async with get_session() as session:
            stmt = select(ReferralLink).where(ReferralLink.id == referral_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_referral_links_by_owner_id(owner_id: int) -> List[ReferralLink]:
        async with get_session() as session:
            stmt = select(ReferralLink).where(ReferralLink.owner_id == owner_id)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_referral_link_by_user_id(user_id: int) -> Optional[ReferralLink]:
        async with get_session() as session:
            stmt = select(ReferralLink).where(ReferralLink.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_all_referral_links() -> List[ReferralLink]:
        async with get_session() as session:
            stmt = select(ReferralLink)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def update_referral_link(
        referral_id: int, **kwargs
    ) -> Optional[ReferralLink]:
        async with get_session() as session:
            stmt = (
                update(ReferralLink)
                .where(ReferralLink.id == referral_id)
                .values(**kwargs)
            )
            await session.execute(stmt)
            await session.commit()
            return await ReferralLinkRequests.get_referral_link_by_id(referral_id)
