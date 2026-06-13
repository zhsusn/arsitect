import asyncio
import json
import os
import subprocess


async def main() -> None:
    prompt = "你好，请简要回复"
    cmd = ["kimi", "--print", "--output-format", "stream-json", "-p", prompt]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    p = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    out, err = await p.communicate()
    with open("kimi_arg_utf8_v4.json", "w", encoding="utf-8") as f:
        f.write(out.decode("utf-8", errors="replace"))
    print(f"rc={p.returncode}")
    print(f"err={err.decode('utf-8', errors='replace')!r}")
    try:
        data = json.loads(out.decode("utf-8", errors="replace"))
        print("JSON OK, text:", data["content"][-1]["text"])
    except Exception as e:
        print("JSON error:", e)


if __name__ == "__main__":
    asyncio.run(main())
