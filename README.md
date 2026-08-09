<div align="center">

# RahSepar | راه‌سپار

**A full-stack intercity bus booking platform with a polished Persian RTL experience.**

![Version 2.0.0](https://img.shields.io/badge/version-2.0.0-0f766e?style=flat-square)
![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![React 19](https://img.shields.io/badge/React-19-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)

[**Explore the live application →**](https://rahsepar.darkube.ir/) · [CLI-focused v1.0.0](https://github.com/MahdiOTET/RahSepar/releases/tag/v1.0.0)

</div>

![RahSepar Persian trip search and ticket results](docs/screenshots/trip-search.png)

RahSepar is a complete demonstration of an Iranian intercity bus booking system. Passengers can discover trips, compare departure times and prices, choose an exact seat, pay from a wallet, and manage their reservations. Operators receive a focused workspace for fleets, schedules, and operational reports.

The React web application and Python CLI both use the same versioned FastAPI REST API. PostgreSQL constraints and transactional service operations protect wallet balances and prevent two passengers from confirming the same seat.

## What RahSepar does

| Area                 | Capabilities                                                                                                                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Passenger experience | Route search, four-way price/departure sorting, live seat maps, wallet-backed booking, cancellation refunds, reservation history, and account balance                                        |
| Operator workspace   | Fleet inspection and JSON import, driver lookup, trip scheduling, capacity tracking, hourly booking reports, monthly bus performance, and busiest-driver reports                             |
| Interface            | Persian-first RTL layout, responsive desktop/mobile navigation, light and dark themes, keyboard-friendly controls, status announcements, reduced-motion support, and focused feedback toasts |
| Platform             | JWT bearer authentication, Pydantic validation, asyncpg connection pooling, transactional business operations, concurrency-safe seat allocation, SQL migrations, and repeatable seeded data  |

## Interface tour

<table>
  <tr>
    <td width="50%" align="center">
      <img src="docs/screenshots/seat-selection.png" alt="RahSepar seat selection dialog showing the bus layout" />
      <br />
      <sub><strong>Seat selection</strong> — a realistic bus layout with clear availability states.</sub>
    </td>
    <td width="50%" align="center">
      <img src="docs/screenshots/my-bookings.png" alt="RahSepar passenger booking history" />
      <br />
      <sub><strong>My Bookings</strong> — reservation details, status, and cancellation in one place.</sub>
    </td>
  </tr>
</table>

![RahSepar operator trip management workspace](docs/screenshots/operator-management.png)

<div align="center"><sub><strong>Operator workspace</strong> — trips, fleet, and reports without a crowded dashboard.</sub></div>

## Quick start

### Try the live demo

Open [rahsepar.darkube.ir](https://rahsepar.darkube.ir/) and choose one of the quick-login accounts:

| Role      | Mobile        | Password      |
| --------- | ------------- | ------------- |
| Passenger | `09800000001` | `DevPass123!` |
| Operator  | `09123456789` | `DevPass123!` |

> [!IMPORTANT]
> These accounts and their data are shared by all demo visitors. Do not enter personal or sensitive information.

- As a **passenger**, search and sort trips, choose a seat, confirm the wallet payment, and manage the reservation under **My Bookings**.
- As an **operator**, open **Management** to inspect trips, manage the fleet, schedule services, and generate reports.

### Run locally with Docker Compose

This is the recommended path. You only need [Git](https://git-scm.com/) and Docker Desktop, or Docker Engine with the Compose plugin.

```powershell
git clone https://github.com/MahdiOTET/RahSepar.git
cd RahSepar
docker compose up --build
```

The command performs the complete startup sequence:

1. Starts PostgreSQL 16.
2. Builds the React frontend.
3. Installs the FastAPI backend in its application image.
4. Waits until PostgreSQL is healthy.
5. Applies every pending SQL migration.
6. Seeds every domain table, including 100,000 confirmed booking records by default.
7. Starts the full application on port `8000`.

The initial seed can take a little longer than later starts. Wait until the logs show that Uvicorn is running, then open:

- Application: <http://127.0.0.1:8000>
- Swagger API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

You can verify the service from PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```text
status
------
ok
```

To stop the stack without deleting PostgreSQL data, press <kbd>Ctrl</kbd>+<kbd>C</kbd> and run:

```powershell
docker compose down
```

### Manual development setup

Use this path when changing the backend or frontend. Install:

- Python 3.11
- Node.js 24
- Docker Desktop with Compose, or an existing PostgreSQL 16 server

Start only the provided PostgreSQL service:

```powershell
docker compose up -d db
```

Create a `.env` file in the repository root:

```dotenv
DATABASE_URL=postgresql://bus_app:bus_app_secret@127.0.0.1:5432/bus_booking
JWT_SECRET=development-only-change-me
```

Prepare and start the backend from Windows PowerShell. These commands use the virtual environment's interpreter directly, so activation is not required:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\venv\Scripts\python.exe -m app migrate
.\venv\Scripts\python.exe -m app seed --bookings 100000
.\venv\Scripts\python.exe -m app serve --reload
```

On Linux or macOS, run the equivalent sequence with:

```bash
python3.11 -m venv venv
./venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
./venv/bin/python -m app migrate
./venv/bin/python -m app seed --bookings 100000
./venv/bin/python -m app serve --reload
```

For a quicker development seed, use a smaller positive `--bookings` value; `100000` mirrors the deployed demonstration dataset.

In a second terminal, start the frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Open the React development server at <http://127.0.0.1:5173>. FastAPI remains at <http://127.0.0.1:8000>, and Vite proxies `/api` and `/health` requests to it automatically.

Docker mode runs migrations and seeding automatically through the container entrypoint. Manual development requires the explicit `migrate` and `seed` commands shown above.

## Architecture

```mermaid
flowchart LR
    Web["React web UI<br/>Persian · RTL"] -->|"JSON · /api/v1"| API["FastAPI routes"]
    CLI["Python CLI"] -->|"HTTP · /api/v1"| API
    API --> Service["Service layer<br/>rules · transactions"]
    Service --> Repository["Repository layer<br/>asyncpg"]
    Repository --> Database[("PostgreSQL 16")]
    Entrypoint["Container entrypoint"] --> Migration["Migrations + repeatable seed"]
    Migration --> Database
```

The production image uses a Node build stage for the web bundle and a Python runtime stage that serves both the REST API and the compiled single-page application. The container runs as a non-root user and exposes `/health` for runtime checks.

```text
app/                 FastAPI routes, services, repositories, schemas, and CLI
frontend/            React application, feature modules, styles, and UI tests
migrations/          Ordered PostgreSQL migrations
tests/               Backend integration and service tests
docker/              Production container entrypoint
compose.yaml         Local PostgreSQL and full-application stack
Dockerfile           Multi-stage production image
```

## REST API

The API base path is `/api/v1`. Protected routes accept a JWT through `Authorization: Bearer <token>`.

| Access           | Endpoints                                                                                    | Purpose                                      |
| ---------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Public           | `POST /auth/login`, `GET /routes`, `GET /tickets`, `GET /trips/{trip_id}/seats`              | Authentication and trip discovery            |
| Passenger        | `GET /users/me`, `GET /bookings`, `POST /bookings`, `DELETE /bookings/{booking_id}`          | Account, booking, and cancellation workflows |
| Operator         | `GET/POST /buses`, `GET /drivers`, `GET/POST /trips`                                         | Fleet and schedule management                |
| Operator reports | `GET /reports/hourly-bookings`, `GET /reports/monthly-buses`, `GET /reports/busiest-drivers` | Operational reporting                        |

Explore the complete request and response schemas in the [live Swagger documentation](https://rahsepar.darkube.ir/docs) or at `/docs` on a local server.

## Data and seeding

RahSepar has seven domain tables: `users`, `profiles`, `routes`, `buses`, `trips`, `bookings`, and `wallet_transactions`. A separate `schema_migrations` table records applied migrations.

The data relationships keep user identity separate from passenger, operator, and driver roles. Bookings connect passenger profiles to trips, while wallet transactions preserve the payment and refund history. PostgreSQL constraints validate statuses and monetary values, and a partial unique index ensures that only one confirmed booking can own a trip's seat.

The repeatable development seeder creates:

- Passenger, operator, and driver profiles
- Iranian routes, buses, and future trips
- Wallet credits and booking payment history
- Available demo tickets
- Up to `SEED_BOOKINGS` generated confirmed bookings (`100000` by default)

## CLI

The CLI talks to the REST API at `http://127.0.0.1:8000/api/v1`, so start the backend before using API-backed commands. Authentication tokens are stored locally in the ignored `.development-token` file.

<details>
<summary><strong>Show CLI examples</strong></summary>

```powershell
# Discover every command and option
.\venv\Scripts\python.exe -m app --help

# Authenticate; the password is requested without echoing it
.\venv\Scripts\python.exe -m app login --mobile 09800000001
.\venv\Scripts\python.exe -m app me

# Discover and book trips
.\venv\Scripts\python.exe -m app tickets --origin "تهران" --destination "مشهد" --sort price_asc

# Replace these numeric IDs with values returned by your requests
.\venv\Scripts\python.exe -m app book --trip-id 2 --seat-number 5
.\venv\Scripts\python.exe -m app cancel --booking-id 123

# Operator reports
.\venv\Scripts\python.exe -m app login --mobile 09123456789
.\venv\Scripts\python.exe -m app hourly-report --date 2026-08-09
.\venv\Scripts\python.exe -m app monthly-bus-report --year 2026 --month 8
.\venv\Scripts\python.exe -m app busiest-drivers --date-from 2026-08-01 --date-to 2026-08-31
```

Use `./venv/bin/python` instead of `.\venv\Scripts\python.exe` on Linux or macOS.

The original CLI and REST API milestone is preserved as [v1.0.0](https://github.com/MahdiOTET/RahSepar/releases/tag/v1.0.0).

</details>

## Tests and quality checks

Install both Python requirement files before running the backend checks:

```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m ruff check app tests
.\venv\Scripts\python.exe -m black --check app tests
```

Run the frontend checks from `frontend/`:

```powershell
npm test
npm run format:check
npm run build
```

Validate or build the production container from the repository root:

```powershell
docker compose config
docker build -t rahsepar:local .
```

## Deployment configuration

The production container applies migrations and repeats the seed before starting Uvicorn. Configure the runtime variables and frontend build argument on the deployment platform:

| Name                   | Phase       | Required | Default            | Purpose                                                                       |
| ---------------------- | ----------- | -------: | ------------------ | ----------------------------------------------------------------------------- |
| `DATABASE_URL`         | Runtime     |      Yes | —                  | PostgreSQL connection string; use the deployment's internal database hostname |
| `JWT_SECRET`           | Runtime     |      Yes | —                  | Secret used to sign access tokens; use a strong production-only value         |
| `SEED_BOOKINGS`        | Runtime     |       No | `100000`           | Number of generated confirmed bookings                                        |
| `PORT`                 | Runtime     |       No | `8000`             | HTTP port used by Uvicorn                                                     |
| `VITE_CLI_RELEASE_URL` | Image build |       No | v1.0.0 release URL | Link shown on the compiled splash screen                                      |

The Compose defaults are intended only for local development. Never reuse `development-only-change-me` as a public deployment secret.

## Versions

| Version                                                             | Focus                                                                                                                                  |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| [v1.0.0](https://github.com/MahdiOTET/RahSepar/releases/tag/v1.0.0) | REST API, PostgreSQL model, repeatable seeding, reports, and Python CLI                                                                |
| v2.0.0                                                              | Responsive Persian RTL React application, passenger and operator workflows, demo quick login, accessibility, and refined result motion |

---

<div align="center">
Designed and developed by <a href="https://github.com/MahdiOTET"><strong>MahdiOTET</strong></a>.
</div>
