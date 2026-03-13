"""
KnowHive FastAPI sidecar — entry point.

Usage:
    uv run python -m app.main --port 18234
"""
import argparse

import uvicorn
from fastapi import FastAPI

APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    app = FastAPI(title="KnowHive Backend", version=APP_VERSION)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": APP_VERSION}

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="KnowHive backend sidecar")
    parser.add_argument(
        "--port",
        type=int,
        default=18234,
        help="Port to listen on (default: 18234)",
    )
    args = parser.parse_args()

    uvicorn.run(
        create_app(),
        host="127.0.0.1",
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
