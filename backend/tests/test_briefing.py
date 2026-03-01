import pytest
from datetime import date

from app.models.news import News


@pytest.mark.asyncio
async def test_briefing_crud(client, auth_headers, db_session):
    # Create some news first
    news1 = News(title="News A", url="https://example.com/brief-a", title_zh="新闻A", summary_zh="摘要A", category="其他", process_status="completed")
    news2 = News(title="News B", url="https://example.com/brief-b", title_zh="新闻B", summary_zh="摘要B", category="其他", process_status="completed")
    db_session.add_all([news1, news2])
    await db_session.commit()
    await db_session.refresh(news1)
    await db_session.refresh(news2)

    # Create briefing
    resp = await client.post("/api/v1/briefings", json={
        "title": "测试快报",
        "date": str(date.today()),
        "news_ids": [news1.id, news2.id],
    }, headers=auth_headers)
    assert resp.status_code == 201
    briefing = resp.json()
    assert len(briefing["items"]) == 2
    briefing_id = briefing["id"]

    # Get briefing
    resp = await client.get(f"/api/v1/briefings/{briefing_id}", headers=auth_headers)
    assert resp.status_code == 200

    # List briefings
    resp = await client.get("/api/v1/briefings", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Update briefing item
    item_id = briefing["items"][0]["id"]
    resp = await client.put(f"/api/v1/briefing-items/{item_id}", json={
        "title": "修改后的标题",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "修改后的标题"

    # Reorder items
    item_ids = [briefing["items"][1]["id"], briefing["items"][0]["id"]]
    resp = await client.post(f"/api/v1/briefing-items/reorder/{briefing_id}", json={
        "item_ids": item_ids,
    }, headers=auth_headers)
    assert resp.status_code == 200

    # Delete briefing
    resp = await client.delete(f"/api/v1/briefings/{briefing_id}", headers=auth_headers)
    assert resp.status_code == 204
