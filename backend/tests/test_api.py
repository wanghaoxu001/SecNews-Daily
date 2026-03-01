import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    resp = await client.get("/api/v1/rss-sources")
    assert resp.status_code in (401, 403)


# ---- RSS Sources CRUD ----
@pytest.mark.asyncio
async def test_rss_source_crud(client, auth_headers):
    # Create
    resp = await client.post(
        "/api/v1/rss-sources",
        json={"name": "Test Feed", "url": "https://example.com/rss"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    source = resp.json()
    source_id = source["id"]
    assert source["name"] == "Test Feed"

    # Read
    resp = await client.get(f"/api/v1/rss-sources/{source_id}", headers=auth_headers)
    assert resp.status_code == 200

    # Update
    resp = await client.put(
        f"/api/v1/rss-sources/{source_id}",
        json={"name": "Updated Feed"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Feed"

    # List
    resp = await client.get("/api/v1/rss-sources", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Delete
    resp = await client.delete(f"/api/v1/rss-sources/{source_id}", headers=auth_headers)
    assert resp.status_code == 204

    # Verify deleted
    resp = await client.get(f"/api/v1/rss-sources/{source_id}", headers=auth_headers)
    assert resp.status_code == 404


# ---- LLM Configs CRUD ----
@pytest.mark.asyncio
async def test_llm_config_crud(client, auth_headers):
    resp = await client.post(
        "/api/v1/llm-configs",
        json={"task_type": "default", "base_url": "http://llm:8080", "api_key": "sk-test", "model": "gpt-4"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    config_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/llm-configs/{config_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.put(
        f"/api/v1/llm-configs/{config_id}",
        json={"model": "gpt-4o"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["model"] == "gpt-4o"

    # Built-in task types cannot be deleted
    resp = await client.delete(f"/api/v1/llm-configs/{config_id}", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_llm_config_ensure_defaults(client, auth_headers):
    resp = await client.post("/api/v1/llm-configs/ensure-defaults", headers=auth_headers)
    assert resp.status_code == 200
    configs = resp.json()
    task_types = {c["task_type"] for c in configs}
    for tt in ["default", "translate", "summarize", "classify", "similarity", "importance", "embedding"]:
        assert tt in task_types


# ---- Task Configs CRUD ----
@pytest.mark.asyncio
async def test_task_config_crud(client, auth_headers):
    resp = await client.post(
        "/api/v1/task-configs",
        json={"name": "rss_fetch", "cron_expression": "0 */2 * * *"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    config_id = resp.json()["id"]

    resp = await client.put(
        f"/api/v1/task-configs/{config_id}",
        json={"cron_expression": "0 */4 * * *"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    resp = await client.delete(f"/api/v1/task-configs/{config_id}", headers=auth_headers)
    assert resp.status_code == 204


# ---- Processing Configs CRUD ----
@pytest.mark.asyncio
async def test_processing_config_crud(client, auth_headers):
    resp = await client.post(
        "/api/v1/processing-configs",
        json={"key": "similarity_threshold", "value": "0.85"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    config_id = resp.json()["id"]

    resp = await client.put(
        f"/api/v1/processing-configs/{config_id}",
        json={"value": "0.9"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "0.9"

    resp = await client.delete(f"/api/v1/processing-configs/{config_id}", headers=auth_headers)
    assert resp.status_code == 204


# ---- Importance Examples CRUD + Bulk Import ----
@pytest.mark.asyncio
async def test_importance_example_crud(client, auth_headers):
    resp = await client.post(
        "/api/v1/importance-examples",
        json={"title": "CVE-2024-1234", "category": "重大漏洞风险提示", "is_important": True, "reason": "Critical RCE"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    example_id = resp.json()["id"]

    resp = await client.get(f"/api/v1/importance-examples/{example_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = await client.delete(f"/api/v1/importance-examples/{example_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_importance_example_bulk_import(client, auth_headers):
    items = [
        {"title": "Example A", "category": "其他", "is_important": False},
        {"title": "Example B", "category": "其他", "is_important": True, "reason": "Important"},
    ]
    resp = await client.post("/api/v1/importance-examples/bulk-import", json=items, headers=auth_headers)
    assert resp.status_code == 201
    assert len(resp.json()) == 2
