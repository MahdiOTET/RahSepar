import argparse
import uvicorn
import asyncio
from app.migrate import run_migrations


def main() -> None:
    parser = argparse.ArgumentParser(description="Bus Ticket Booking Application")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="Start the RestAPI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--reload", action="store_true")

    commands.add_parser("migrate", help="Apply Pending Database Migrations")

    args = parser.parse_args()

    if args.command == "serve":
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
    elif args.command == "migrate":
        asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
