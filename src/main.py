import asyncio
from src.cli.cli import app


def main():
    asyncio.run(app())

if __name__ == "__main__":
    main()