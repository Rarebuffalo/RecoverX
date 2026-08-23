import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Merchant, Customer


async def resolve_merchant(db: AsyncSession, account_id: str | None = None) -> Merchant | None:
    """Resolves merchant by Razorpay account_id, or falls back to the default active merchant."""
    if account_id:
        query = select(Merchant).where(Merchant.razorpay_account_id == account_id).limit(1)
        result = await db.execute(query)
        merchant = result.scalar_one_or_none()
        if merchant:
            return merchant

    # Fallback to the first active merchant in the system
    query = select(Merchant).where(Merchant.is_active.is_(True)).order_by(Merchant.created_at.asc()).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_or_create_customer(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    email: str | None,
    phone: str | None = None,
    name: str | None = None,
) -> Customer:
    """Gets an existing customer by (merchant_id, email) or creates a new customer record."""
    clean_email = email.strip().lower() if email else f"customer_{uuid.uuid4().hex[:8]}@example.com"
    
    query = select(Customer).where(
        Customer.merchant_id == merchant_id,
        Customer.email == clean_email,
    ).limit(1)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        customer = Customer(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            email=clean_email,
            phone=phone,
            name=name or clean_email.split("@")[0].capitalize(),
            lifetime_value_inr=Decimal("0.00"),
            total_orders=0,
            successful_orders=0,
        )
        db.add(customer)
        await db.flush()
        
    return customer
