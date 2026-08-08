import argparse
import uvicorn
import asyncio
import json
import httpx
from getpass import getpass
from pathlib import Path
from app.migrate import run_migrations
from app.seed import seed_development_data

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

TOKEN_FILE = Path(__file__).resolve().parent.parent / ".development-token"


def login_via_api(mobile: str, password: str) -> None:
    try:
        response = httpx.post(
            f"{API_BASE_URL}/auth/login",
            json={"mobile": mobile, "password": password},
            timeout=10,
        )

    except httpx.RequestError as err:
        print(f"Could not connect to backend {err}")
        return

    if response.is_error:
        print(f"Login failed ({response.status_code}):")
        print(response.text)
        return

    token = response.json()["access_token"]
    TOKEN_FILE.write_text(token, encoding="utf-8")

    print("Login successful.")
    print("Development token saved")


def show_current_user() -> None:
    if not TOKEN_FILE.exists():
        print("No token found. Run the login command first.")
        return
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    try:
        response = httpx.get(
            f"{API_BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

    except httpx.RequestError as err:
        print(f"Could not connect to backend: {err}")
        return

    if response.is_error:
        print(f"Request failed ({response.status_code}):")
        print(response.text)
        return

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Bus Ticket Booking Application")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="Start the RestAPI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--reload", action="store_true")

    commands.add_parser("migrate", help="Apply Pending Database Migrations")

    commands.add_parser("seed", help="Insert Development Data")

    login_command = commands.add_parser("login", help="Log in Thrugh the REST API")
    login_command.add_argument("--mobile", required=True)

    commands.add_parser("me", help="Display the Authenricated User Information")
    args = parser.parse_args()

    if args.command == "serve":
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
    elif args.command == "migrate":
        asyncio.run(run_migrations())
    elif args.command == "seed":
        asyncio.run(seed_development_data())
    elif args.command == "login":
        password = getpass("Password: ")
        login_via_api(args.mobile, password)
    elif args.command == "me":
        show_current_user()


if __name__ == "__main__":
    main()
