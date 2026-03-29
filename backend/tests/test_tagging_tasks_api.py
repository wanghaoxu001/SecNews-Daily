import io

import pytest


CSV_CONTENT = """title,summary,category,reason
Apache 漏洞预警,公开 POC 已出现,重大漏洞风险提示,已有利用链
常规版本更新,,其他,例行更新
"""


def make_csv_file(content: str = CSV_CONTENT) -> dict[str, tuple[str, io.BytesIO, str]]:
    return {
        "file": (
            "importance-examples.csv",
            io.BytesIO(content.encode("utf-8")),
            "text/csv",
        )
    }


@pytest.mark.asyncio
async def test_create_tagging_task_accepts_long_title(client, auth_headers):
    long_title = "A" * 550
    content = f"title,summary,category,reason\n{long_title},摘要,重大漏洞风险提示,\n"

    resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file(content),
        headers=auth_headers,
    )

    assert resp.status_code == 201
    assert resp.json()["current_item"]["title"] == long_title


@pytest.mark.asyncio
async def test_create_tagging_task_success(client, auth_headers):
    resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file(),
        headers=auth_headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["task"]["original_file_name"] == "importance-examples.csv"
    assert data["task"]["total_count"] == 2
    assert data["task"]["status"] == "in_progress"
    assert data["task"]["labeled_count"] == 0
    assert data["current_item"]["row_index"] == 0
    assert data["current_item"]["title"] == "Apache 漏洞预警"


@pytest.mark.asyncio
async def test_list_tagging_tasks_success(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file(),
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    resp = await client.get("/api/v1/tagging-tasks", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["original_file_name"] == "importance-examples.csv"


@pytest.mark.asyncio
async def test_create_tagging_task_requires_auth(client):
    resp = await client.post("/api/v1/tagging-tasks", files=make_csv_file())
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_tagging_task_rejects_invalid_csv(client, auth_headers):
    resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file("title,summary,reason\nfoo,bar,baz\n"),
        headers=auth_headers,
    )

    assert resp.status_code == 422
    assert "category" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_tagging_task_lifecycle_and_import(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file(),
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["task"]["id"]
    first_item_id = create_resp.json()["current_item"]["id"]

    mark_resp = await client.patch(
        f"/api/v1/tagging-tasks/{task_id}/items/{first_item_id}",
        json={"is_important": True},
        headers=auth_headers,
    )
    assert mark_resp.status_code == 200
    assert mark_resp.json()["item"]["is_important"] is True
    assert mark_resp.json()["task"]["labeled_count"] == 1

    cursor_resp = await client.patch(
        f"/api/v1/tagging-tasks/{task_id}/cursor",
        json={"current_index": 1},
        headers=auth_headers,
    )
    assert cursor_resp.status_code == 200
    assert cursor_resp.json()["task"]["current_index"] == 1
    assert cursor_resp.json()["current_item"]["row_index"] == 1

    detail_resp = await client.get(f"/api/v1/tagging-tasks/{task_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["task"]["labeled_count"] == 1
    assert detail_resp.json()["task"]["current_index"] == 1

    import_before_complete = await client.post(
        f"/api/v1/tagging-tasks/{task_id}/import",
        headers=auth_headers,
    )
    assert import_before_complete.status_code == 409

    items = detail_resp.json()["items"]
    second_item = next(item for item in items if item["row_index"] == 1)
    second_mark_resp = await client.patch(
        f"/api/v1/tagging-tasks/{task_id}/items/{second_item['id']}",
        json={"is_important": False},
        headers=auth_headers,
    )
    assert second_mark_resp.status_code == 200

    complete_resp = await client.post(
        f"/api/v1/tagging-tasks/{task_id}/complete",
        headers=auth_headers,
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["task"]["status"] == "completed"

    import_resp = await client.post(
        f"/api/v1/tagging-tasks/{task_id}/import",
        headers=auth_headers,
    )
    assert import_resp.status_code == 200
    data = import_resp.json()
    assert data["task"]["status"] == "imported"
    assert data["imported_count"] == 2
    assert data["skipped_count"] == 0

    examples_resp = await client.get("/api/v1/importance-examples", headers=auth_headers)
    assert examples_resp.status_code == 200
    titles = {item["title"] for item in examples_resp.json()}
    assert {"Apache 漏洞预警", "常规版本更新"}.issubset(titles)


@pytest.mark.asyncio
async def test_import_tagging_task_skips_duplicate_examples(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file(),
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["task"]["id"]

    detail_resp = await client.get(f"/api/v1/tagging-tasks/{task_id}", headers=auth_headers)
    items = detail_resp.json()["items"]

    for item in items:
        mark_resp = await client.patch(
            f"/api/v1/tagging-tasks/{task_id}/items/{item['id']}",
            json={"is_important": item["row_index"] == 0},
            headers=auth_headers,
        )
        assert mark_resp.status_code == 200

    complete_resp = await client.post(
        f"/api/v1/tagging-tasks/{task_id}/complete",
        headers=auth_headers,
    )
    assert complete_resp.status_code == 200

    first_import = await client.post(
        f"/api/v1/tagging-tasks/{task_id}/import",
        headers=auth_headers,
    )
    assert first_import.status_code == 200

    second_task_resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file(),
        headers=auth_headers,
    )
    second_task_id = second_task_resp.json()["task"]["id"]
    second_detail = await client.get(f"/api/v1/tagging-tasks/{second_task_id}", headers=auth_headers)
    for item in second_detail.json()["items"]:
        mark_resp = await client.patch(
            f"/api/v1/tagging-tasks/{second_task_id}/items/{item['id']}",
            json={"is_important": item["row_index"] == 0},
            headers=auth_headers,
        )
        assert mark_resp.status_code == 200

    complete_second = await client.post(
        f"/api/v1/tagging-tasks/{second_task_id}/complete",
        headers=auth_headers,
    )
    assert complete_second.status_code == 200

    second_import = await client.post(
        f"/api/v1/tagging-tasks/{second_task_id}/import",
        headers=auth_headers,
    )
    assert second_import.status_code == 200
    assert second_import.json()["imported_count"] == 0
    assert second_import.json()["skipped_count"] == 2


@pytest.mark.asyncio
async def test_complete_tagging_task_requires_full_labeling(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/tagging-tasks",
        files=make_csv_file(),
        headers=auth_headers,
    )
    task_id = create_resp.json()["task"]["id"]

    complete_resp = await client.post(
        f"/api/v1/tagging-tasks/{task_id}/complete",
        headers=auth_headers,
    )
    assert complete_resp.status_code == 409
