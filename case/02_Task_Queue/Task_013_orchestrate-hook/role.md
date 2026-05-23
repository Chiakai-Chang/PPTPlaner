# Role: Integration Engineer

You wire the video pipeline into scripts/orchestrate.py with the smallest possible change.
One conditional block at the end of the main flow only.
MUST NOT refactor or modify any existing logic in orchestrate.py.
Gate: config.get("video", {}).get("enabled", False)
