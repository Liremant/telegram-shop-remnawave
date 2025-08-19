from sqlalchemy import select, update
from datetime import datetime
from typing import Optional, List
from database.db import User, Sublink, Invoice, ReferralLink,get_session


class UserRequests:
    @staticmethod
    async def create_user(username: str, telegram_id: int, name: str,locale:str) -> bool:
        async with get_session() as session:
            existing = await UserRequests.get_user_by_telegram_id(telegram_id)
            if existing:
                return False

            user = User(username=username, telegram_id=telegram_id, name=name,locale=locale)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return True

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

    @staticmethod
    async def get_all_users() -> List[User]:
        async with get_session() as session:
            stmt = select(User)
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def update_user(user_id: int, **kwargs) -> Optional[User]:
        async with get_session() as session:
            stmt = update(User).where(User.id == user_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()
            return await UserRequests.get_user_by_id(user_id)



class SublinkRequests:
    @staticmethod
    async def create_sublink(
        link: str, expires_at: datetime, username: str, user_id: int, rate: int
    ) -> Sublink:
        async with get_session() as session:
            sublink = Sublink(
                link=link,
                expires_at=expires_at,
                username=username,
                user_id=user_id,
                rate=rate,
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




class InvoiceRequests:
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

class ReferralLinkRequests:
    @staticmethod
    async def create_referral_link(
        link: str, owner_id: int, user_id: int
    ) -> ReferralLink:
        async with get_session() as session:
            referral_link = ReferralLink(
                link=link,
                owner_id=owner_id,
                user_id=user_id,
            )
            session.add(referral_link)
            await session.commit()
            await session.refresh(referral_link)
            return referral_link

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
    async def update_referral_link(referral_id: int, **kwargs) -> Optional[ReferralLink]:
        async with get_session() as session:
            stmt = update(ReferralLink).where(ReferralLink.id == referral_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()
            return await ReferralLinkRequests.get_referral_link_by_id(referral_id)

