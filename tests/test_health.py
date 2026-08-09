import httpx

from app.main import create_app


async def test_health_endpoint(api_client: httpx.AsyncClient) -> None:
    response = await api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_frontend_files_and_spa_fallback(tmp_path) -> None:
    frontend_directory = tmp_path / "dist"
    assets_directory = frontend_directory / "assets"
    assets_directory.mkdir(parents=True)
    (frontend_directory / "index.html").write_text(
        "<!doctype html><title>Rahsepar</title>",
        encoding="utf-8",
    )
    (assets_directory / "app.css").write_text("body {}", encoding="utf-8")

    application = create_app(frontend_directory)
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        home = await client.get("/")
        client_route = await client.get("/bookings")
        asset = await client.get("/assets/app.css")
        missing_api = await client.get("/api/v1/does-not-exist")

    assert home.status_code == 200
    assert "Rahsepar" in home.text
    assert client_route.status_code == 200
    assert "Rahsepar" in client_route.text
    assert asset.status_code == 200
    assert asset.text == "body {}"
    assert missing_api.status_code == 404
    assert missing_api.headers["content-type"].startswith("application/json")
