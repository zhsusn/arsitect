"""Standalone validation of the arch fix pipeline."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import websockets

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("gbk", errors="replace"))

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/api/v1/cli/ws"
PROJECT_ID = "sdlc-visualizer"
LOG_FILE = Path("D:/srccode/arsitect/backend/test_arch_fix_log.jsonl")


async def create_session() -> str:
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            f"{BASE_URL}/api/v1/cli/sessions",
            json={"project_id": PROJECT_ID, "mode": "arch"},
        )
        r.raise_for_status()
        return r.json()["id"]


async def generate_fix_plan() -> dict:
    issue = {
        "issue_id": "CON-C2M-frontend-spa",
        "source": "validator",
        "rule_id": "CON-C2M-001",
        "severity": "WARNING",
        "message": "容器 React 19 SPA 在代码中未找到对应模块",
        "c4_node_id": "frontend-spa",
        "code_entity_id": "",
        "fix_hint": "在 backend/app/ 或 frontend/src/ 下创建 frontend-spa 目录；或在设计文档中修正容器定义",
        "fix_action": "UPDATE_CODE",
        "root_cause": "CODE_MISSING",
        "auto_fixable": False,
        "confidence": "LOW",
        "extra": {},
    }
    req = {
        "issues": [issue],
        "context": {
            "strategy_prompt": "请分析为什么C4设计中定义的容器在代码中找不到对应模块，并给出最小修复方案。"
        },
    }
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(
            f"{BASE_URL}/api/v1/c4/governance/fix-plan?project_id={PROJECT_ID}",
            json=req,
        )
        r.raise_for_status()
        return r.json()


async def main() -> None:
    session_id = await create_session()
    _safe_print(f"created session: {session_id}")

    plan = await generate_fix_plan()
    _safe_print(f"generated plan with {len(plan.get('plans', []))} plan items")

    LOG_FILE.write_text("", encoding="utf-8")

    async with websockets.connect(f"{WS_URL}/{session_id}") as ws:
        _safe_print("websocket connected")

        cmd = {
            "type": "command",
            "session_id": session_id,
            "payload": {
                "command": "apply_arch_fix_plan",
                "metadata": {
                    "action": "apply_arch_fix_plan",
                    "project_id": PROJECT_ID,
                    "plan": plan,
                    "strategy_prompt": plan.get("strategy_prompt", ""),
                },
            },
        }
        await ws.send(json.dumps(cmd, ensure_ascii=False))
        _safe_print("sent apply_arch_fix_plan")

        deadline = asyncio.get_event_loop().time() + 120
        while asyncio.get_event_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
            except asyncio.TimeoutError:
                continue

            msg = json.loads(raw)
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

            msg_type = msg.get("type")
            payload = msg.get("payload") or {}
            text = payload.get("text") or ""
            card = payload.get("card")

            _safe_print(f"[{msg_type}] {text[:120] if text else '(card)'}")

            if msg_type == "card" and card and card.get("type") == "arch-decision":
                _safe_print("received arch-decision card, sending fix action")
                change = card.get("data", {})
                action_msg = {
                    "type": "action",
                    "session_id": session_id,
                    "payload": {
                        "command": "fix",
                        "metadata": {
                            "change": change,
                            "project_id": PROJECT_ID,
                            "strategy_prompt": plan.get("strategy_prompt", ""),
                        },
                    },
                }
                await ws.send(json.dumps(action_msg, ensure_ascii=False))

            if msg_type == "done":
                _safe_print("received done")

    _safe_print(f"log saved to {LOG_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
