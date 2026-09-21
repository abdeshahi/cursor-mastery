import asyncio
import logging

from app.bot.handlers import run_bot


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_bot())


if __name__ == '__main__':
    main()
