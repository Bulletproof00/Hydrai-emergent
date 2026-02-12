import asyncio

from packages.core.config.settings import get_settings
from packages.core.db.session import SessionLocal
from packages.core.services.ingestion import upsert_instrument


async def main() -> None:
    settings = get_settings()
    symbols = [s.strip() for s in settings.symbols.split(",") if s.strip()]
    async with SessionLocal() as session:
        for symbol in symbols:
            await upsert_instrument(session, symbol=symbol, market_type="spot")
            await upsert_instrument(session, symbol=symbol, market_type="future")
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
