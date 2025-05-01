import asyncio
from parsers.tg_client import TGClient

if __name__ == "__main__":
    asyncio.run(TGClient().start())
