"""验证 AI CLI 修复终端中 LLM 分支的 Kimi CLI 输出与 thinking 流。"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import websockets

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/api/v1/cli/ws"
PROJECT_ID = "sdlc-visualizer"
LOG_FILE = Path("D:/srccode/arsitect/verify_llm_ws_log.jsonl")


async def create_session() -> str:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/api/v1/cli/sessions",
            json={"project_id": PROJECT_ID, "mode": "arch"},
        )
        r.raise_for_status()
        data = r.json()
        return data["id"]


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
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/api/v1/c4/governance/fix-plan?project_id={PROJECT_ID}",
            json=req,
        )
        r.raise_for_status()
        return r.json()


async def run_verification() -> None:
    session_id = await create_session()
    print(f"created session: {session_id}")

    plan = await generate_fix_plan()
    print(f"generated plan with {len(plan.get('plans', []))} plan items")

    LOG_FILE.write_text("", encoding="utf-8")

    async with websockets.connect(f"{WS_URL}/{session_id}") as ws:
        print("websocket connected")

        # 发送 apply_arch_fix_plan 命令
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
        print("sent apply_arch_fix_plan")

        pending_card: dict | None = None

        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=300)
            except asyncio.TimeoutError:
                print("timeout waiting for message")
                break

            msg = json.loads(raw)
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

            msg_type = msg.get("type")
            payload = msg.get("payload") or {}
            text = payload.get("text") or ""
            card = payload.get("card")

            safe_text = text[:120].encode("gbk", "ignore").decode("gbk", "ignore") if text else ""
            print(f"[{msg_type}] {safe_text}")

            if msg_type == "card" and card and card.get("type") == "arch-decision":
                pending_card = card
                print("received arch-decision card, sending fix action")
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
                print("received done, keep listening for LLM outputs...")

        # 再给 60 秒，等待 handle_change_action / LLM 流式输出
        print("waiting extra 60s for LLM results")
        deadline = asyncio.get_event_loop().time() + 60
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
            safe_text = text[:120].encode("gbk", "ignore").decode("gbk", "ignore") if text else ""
            print(f"[{msg_type}] {safe_text}")

    print(f"log saved to {LOG_FILE}")


if __name__ == "__main__":
    asyncio.run(run_verification())
