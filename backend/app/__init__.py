"""Application package.

On Windows we must use ProactorEventLoop so that asyncio can spawn subprocesses
(required by the Kimi CLI LLM gateway). Setting the policy here guarantees it is
applied regardless of which entry point (main.py or app.main.py) uvicorn loads.
"""

from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
