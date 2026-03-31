"""Process entrypoint for local execution."""

from __future__ import annotations

import uvicorn

from api.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.reload_enabled,
    )
