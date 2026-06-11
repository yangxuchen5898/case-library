#!/usr/bin/env python3
"""Opt-in smoke check for the real AI review backend path.

This script intentionally is not part of the default gate. It requires explicit
AI configuration and verifies that the backend `/api/cases/{id}/ai-review`
endpoint can call the configured OpenAI-compatible provider through the server.
It never prints the API key, base URL, or prompt text.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))

import main
from ai_client import AISettings
from database import create_case, create_user, delete_case, delete_user, get_user_by_username
from fastapi.testclient import TestClient

USERNAME = f"real_ai_smoke_{uuid4().hex[:10]}"
PASSWORD = "RealAiSmoke123!"


def auth(username: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {main.create_auth_token(username)}"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real AI review backend smoke.")
    parser.add_argument(
        "--require-config",
        action="store_true",
        help="Fail instead of skipping when AI env is disabled or incomplete.",
    )
    return parser.parse_args()


def check_settings(require_config: bool) -> AISettings | None:
    settings = AISettings.from_env()
    if not settings.enabled:
        message = "skip: AI_REVIEW_ENABLED is false"
        if require_config:
            raise SystemExit(message)
        print(message)
        return None
    if not settings.configured():
        message = "skip: AI service is unconfigured"
        if require_config:
            raise SystemExit(message)
        print(message)
        return None
    print(f"real AI smoke enabled: model={settings.default_model}")
    return settings


def main_smoke() -> int:
    args = parse_args()
    settings = check_settings(args.require_config)
    if settings is None:
        return 0

    client = TestClient(main.app)
    case_id: int | None = None
    try:
        if get_user_by_username(USERNAME):
            delete_user(USERNAME)
        create_user(
            username=USERNAME,
            password=PASSWORD,
            role="normal",
            nickname="Real AI Smoke",
            must_change_password=False,
            status="active",
        )
        case_id = create_case(
            {
                "title": "真实 AI 自查 smoke 案例",
                "type": "TYPE_A",
                "theme": "铸魂育人",
                "content": "第一段说明课程思政案例背景。\n第二段说明来源材料仍需补充具体时间和对象。",
                "source_material": "来源材料：学院新闻摘录、课堂反馈摘要。",
                "author": "Real AI Smoke",
                "owner_username": USERNAME,
                "department": "马克思主义学院",
                "status": "draft",
            }
        )
        response = client.post(f"/api/cases/{case_id}/ai-review", json={}, headers=auth(USERNAME))
        payload = response.json()
        status = payload.get("status", "ok" if response.status_code == 200 else "unknown")
        print(f"backend ai-review response: http={response.status_code} status={status}")
        if response.status_code != 200:
            print(f"detail={payload.get('detail', '')}")
            return 1

        data = payload.get("data") or {}
        comments = data.get("comments") or []
        summary = data.get("summary") or {}
        version = data.get("version") or {}
        if not isinstance(comments, list) or not isinstance(summary, dict) or not version:
            print("invalid response shape from backend ai-review")
            return 1
        print(
            "real AI smoke passed: "
            f"version=v{version.get('version_number')} comments={len(comments)}"
        )
        return 0
    finally:
        if case_id is not None:
            delete_case(case_id)
        delete_user(USERNAME)


if __name__ == "__main__":
    raise SystemExit(main_smoke())
