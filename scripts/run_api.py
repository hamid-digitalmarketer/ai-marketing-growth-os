"""Local API runner: uvicorn entrypoint for the Growth OS backend.

Usage::

    python scripts/run_api.py
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("GROWTH_OS_HOST", "0.0.0.0")
    port = int(os.getenv("GROWTH_OS_PORT", "8000"))
    uvicorn.run("backend.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
