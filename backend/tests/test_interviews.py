"""Tests for the interview API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_interview(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Create a new interview session."""
    resp = await client.post(
        "/api/interviews/",
        json={"jd_text": "Senior Python Developer at TechCo"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["jd_text"] == "Senior Python Developer at TechCo"
    assert data["status"] == "created"
    assert data["interview_type"] == "full"


@pytest.mark.asyncio
async def test_create_interview_unauthenticated(
    client: AsyncClient,
) -> None:
    """Creating an interview without auth returns 401."""
    resp = await client.post("/api/interviews/", json={})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_interviews(
    client: AsyncClient, auth_headers: dict
) -> None:
    """List the current user's interviews."""
    # Create 2 interviews
    await client.post(
        "/api/interviews/",
        json={"jd_text": "Role 1"},
        headers=auth_headers,
    )
    await client.post(
        "/api/interviews/",
        json={"jd_text": "Role 2"},
        headers=auth_headers,
    )

    resp = await client.get("/api/interviews/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["interviews"]) == 2


@pytest.mark.asyncio
async def test_interview_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Accessing a non-existent interview returns 404."""
    resp = await client.get(
        "/api/interviews/non-existent-id/next-question",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_start_interview_missing_resume(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Starting without a resume returns 400."""
    create_resp = await client.post(
        "/api/interviews/",
        json={"jd_text": "SDE Role"},
        headers=auth_headers,
    )
    interview_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/interviews/{interview_id}/start",
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "resume" in resp.json()["detail"].lower()
