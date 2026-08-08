import argparse
import asyncio
import json
from getpass import getpass
from pathlib import Path

import httpx
import uvicorn

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


def list_tickets_via_api(
    origin: str | None, destination: str | None, sort: str, limit: int, offset: int
) -> None:
    parameters: dict[str, str | int] = {
        "sort": sort,
        "limit": limit,
        "offset": offset,
    }

    if origin:
        parameters["origin"] = origin

    if destination:
        parameters["destination"] = destination

    try:
        response = httpx.get(f"{API_BASE_URL}/tickets", params=parameters, timeout=10)

    except httpx.RequestError as err:
        print(f"Could not connect to backend: {err}")
        return

    if response.is_error:
        print(f"Request failed ({response.status_code}):")
        print(response.text)
        return

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def book_trip_via_api(trip_id: int, seat_number: int) -> None:
    if not TOKEN_FILE.exists():
        print("No token found. Run the login command first.")
        return

    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    try:
        response = httpx.post(
            f"{API_BASE_URL}/bookings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "trip_id": trip_id,
                "seat_number": seat_number,
            },
            timeout=10,
        )

    except httpx.RequestError as err:
        print(f"Could not connect to backend: {err}")
        return

    if response.is_error:
        print(f"Booking failed ({response.status_code}):")
        print(response.text)
        return

    print("Booking created successfully.")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def cancel_booking_via_api(booking_id: int) -> None:
    if not TOKEN_FILE.exists():
        print("No token found. Run the login command first.")
        return

    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    try:
        response = httpx.delete(
            f"{API_BASE_URL}/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

    except httpx.RequestError as err:
        print(f"Could not connect to backend {err}")
        return

    if response.is_error:
        print(f"Cancellation failed ({response.status_code}):")
        print(response.text)
        return

    print("Booking cancelled successfully.")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def import_buses_via_api(file_path: Path) -> None:
    if not TOKEN_FILE.exists():
        print("No token found. Run the login command first.")
        return

    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    try:
        request_data = json.loads(file_path.read_text(encoding="utf-8"))

    except OSError as err:
        print(f"Could not read import file: {err}")
        return

    except json.JSONDecodeError as err:
        print(f"Import file contains invalid JSON: {err}")
        return

    try:
        response = httpx.post(
            f"{API_BASE_URL}/buses",
            headers={"Authorization": f"Bearer {token}"},
            json=request_data,
            timeout=30,
        )

    except httpx.RequestError as err:
        print(f"Could not connect to backend: {err}")
        return

    if response.is_error:
        print(f"Bus import failed ({response.status_code}):")
        print(response.text)
        return

    print("Buses imported successfully.")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def create_trip_via_api(
    bus_id: int,
    driver_profile_id: int,
    departure_time: str,
    arrival_time: str,
    price: str,
) -> None:
    if not TOKEN_FILE.exists():
        print("No token found. Run the login command first.")
        return

    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    try:
        response = httpx.post(
            f"{API_BASE_URL}/trips",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "bus_id": bus_id,
                "driver_profile_id": driver_profile_id,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "price": price,
            },
            timeout=10,
        )

    except httpx.RequestError as err:
        print(f"Could not connect to backend: {err}")
        return

    if response.is_error:
        print(f"Trip creation failed ({response.status_code}):")
        print(response.text)
        return

    print("Trip created successfully.")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def show_operator_report(path: str, parameters: dict[str, str | int]) -> None:
    if not TOKEN_FILE.exists():
        print("No token found. Run the login command first.")
        return

    token = TOKEN_FILE.read_text(encoding="utf-8").strip()

    try:
        response = httpx.get(
            f"{API_BASE_URL}/{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=parameters,
            timeout=30,
        )

    except httpx.RequestError as err:
        print(f"Could not connect to backend: {err}")
        return

    if response.is_error:
        print(f"Report request failed ({response.status_code}):")
        print(response.text)
        return

    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Bus Ticket Booking Application")
    commands = parser.add_subparsers(dest="command", required=True)

    serve = commands.add_parser("serve", help="Start the REST API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--reload", action="store_true")

    commands.add_parser("migrate", help="Apply pending database migrations")

    seed_command = commands.add_parser("seed", help="Insert development data")
    seed_command.add_argument("--bookings", type=int, default=100_000)

    login_command = commands.add_parser("login", help="Log in through the REST API")
    login_command.add_argument("--mobile", required=True)

    commands.add_parser("me", help="Display authenticated user information")

    tickets_command = commands.add_parser("tickets", help="List available tickets")
    tickets_command.add_argument("--origin")
    tickets_command.add_argument("--destination")
    tickets_command.add_argument(
        "--sort", choices=["price_asc", "price_desc"], default="price_asc"
    )
    tickets_command.add_argument("--limit", type=int, default=20)
    tickets_command.add_argument("--offset", type=int, default=0)

    book_command = commands.add_parser("book", help="Book a seat")
    book_command.add_argument("--trip-id", type=int, required=True)
    book_command.add_argument("--seat-number", type=int, required=True)

    cancel_command = commands.add_parser("cancel", help="Cancel a booking")
    cancel_command.add_argument("--booking-id", type=int, required=True)

    import_buses_command = commands.add_parser(
        "import-buses", help="Import buses from a JSON file"
    )
    import_buses_command.add_argument("--file", type=Path, required=True)

    create_trip_command = commands.add_parser(
        "create-trip", help="Create a scheduled trip"
    )
    create_trip_command.add_argument("--bus-id", type=int, required=True)
    create_trip_command.add_argument("--driver-profile-id", type=int, required=True)
    create_trip_command.add_argument("--departure-time", required=True)
    create_trip_command.add_argument("--arrival-time", required=True)
    create_trip_command.add_argument("--price", required=True)

    hourly_report_command = commands.add_parser(
        "hourly-report", help="Show confirmed bookings by Tehran hour"
    )
    hourly_report_command.add_argument("--date", required=True)

    monthly_bus_report_command = commands.add_parser(
        "monthly-bus-report", help="Show monthly bus performance"
    )
    monthly_bus_report_command.add_argument("--year", type=int, required=True)
    monthly_bus_report_command.add_argument("--month", type=int, required=True)

    busiest_drivers_command = commands.add_parser(
        "busiest-drivers", help="Show the busiest drivers for a date range"
    )
    busiest_drivers_command.add_argument("--date-from", required=True)
    busiest_drivers_command.add_argument("--date-to", required=True)
    busiest_drivers_command.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "serve":
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
    elif args.command == "migrate":
        asyncio.run(run_migrations())
    elif args.command == "seed":
        asyncio.run(seed_development_data(booking_count=args.bookings))
    elif args.command == "login":
        password = getpass("Password: ")
        login_via_api(args.mobile, password)
    elif args.command == "me":
        show_current_user()
    elif args.command == "tickets":
        list_tickets_via_api(
            origin=args.origin,
            destination=args.destination,
            sort=args.sort,
            limit=args.limit,
            offset=args.offset,
        )
    elif args.command == "book":
        book_trip_via_api(trip_id=args.trip_id, seat_number=args.seat_number)
    elif args.command == "cancel":
        cancel_booking_via_api(booking_id=args.booking_id)
    elif args.command == "import-buses":
        import_buses_via_api(file_path=args.file)
    elif args.command == "create-trip":
        create_trip_via_api(
            bus_id=args.bus_id,
            driver_profile_id=args.driver_profile_id,
            departure_time=args.departure_time,
            arrival_time=args.arrival_time,
            price=args.price,
        )
    elif args.command == "hourly-report":
        show_operator_report(
            path="reports/hourly-bookings",
            parameters={"report_date": args.date},
        )
    elif args.command == "monthly-bus-report":
        show_operator_report(
            path="reports/monthly-buses",
            parameters={"year": args.year, "month": args.month},
        )
    elif args.command == "busiest-drivers":
        show_operator_report(
            path="reports/busiest-drivers",
            parameters={
                "date_from": args.date_from,
                "date_to": args.date_to,
                "limit": args.limit,
            },
        )


if __name__ == "__main__":
    main()
