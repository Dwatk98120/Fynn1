"""Respond to /health while large speech modules are importing.

The Windows launcher used to import torch/transformers before Uvicorn could
bind its socket. On slower PCs this made startup appear dead for minutes.
This lightweight ASGI gateway binds localhost/LAN first, then imports the
original FastAPI app off the event loop and hands all real requests to it.

It does not claim speech readiness while the module or models are loading.
The original Android routes, Phase 2 queued jobs and Phase 3 learning routes
remain owned by server.main, unchanged once initialized.
"""
from __future__ import annotations

import importlib
import json
import logging
import threading
import time

LOG = logging.getLogger("hearlium.startup")


class BootstrapServer:
    def __init__(self, loader=None):
        self._loader = loader or self._load_main
        self._app = None
        self._error = None
        self._started = None
        self._stage = "Waiting for server startup"
        self._lock = threading.RLock()
        self._launch_started = False

    @staticmethod
    def _load_main():
        main = importlib.import_module("main")
        # The FastAPI lifespan of this imported app is not invoked directly;
        # its only current startup handler preloads speech models on a daemon.
        # Start that handler explicitly, preserving the Phase 2 cold-start fix.
        if hasattr(main, "start_background_model_warmup"):
            main.start_background_model_warmup()
        return main.app

    def start(self):
        with self._lock:
            if self._launch_started:
                return
            self._launch_started = True
            self._started = time.monotonic()
            self._stage = "Importing speech analysis modules"
            thread = threading.Thread(target=self._load, name="HearliumStartupImport", daemon=True)
            thread.start()

    def _load(self):
        begin = time.monotonic()
        LOG.info("Importing Hearlium analysis application")
        try:
            application = self._loader()
            if not callable(application):
                raise RuntimeError("analysis_app_not_callable")
            with self._lock:
                self._app = application
                self._stage = "Local API serving"
            LOG.info("API import completed in %.2fs", time.monotonic() - begin)
        except Exception as exc:
            with self._lock:
                self._error = f"{type(exc).__name__}: {exc}"[:300]
                self._stage = "Unable to initialize speech analysis"
            LOG.exception("Hearlium background API import failed")

    def snapshot(self):
        with self._lock:
            return {
                "ok": self._app is not None,
                "serverPhase": "serving" if self._app else ("failed" if self._error else "initializing"),
                "stage": self._stage,
                "elapsedSeconds": round(time.monotonic() - self._started, 1) if self._started else 0,
                "error": self._error,
            }

    @staticmethod
    async def _respond(send, status, body, extra_headers=()):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = [(b"content-type", b"application/json"), (b"cache-control", b"no-store")]
        headers.extend(extra_headers)
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": payload})

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                event = await receive()
                if event["type"] == "lifespan.startup":
                    self.start()
                    await send({"type": "lifespan.startup.complete"})
                elif event["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
            return

        with self._lock:
            application = self._app
        if application is not None:
            await application(scope, receive, send)
            return

        if scope["type"] == "http":
            path = scope.get("path", "")
            state = self.snapshot()
            if path in ("/health", "/v1/analysis-status"):
                # HTTP socket is listening, but 200 is NOT model or API readiness.
                await self._respond(send, 200, state)
            else:
                await self._respond(send, 503, {
                    "detail": "parent_pc_initializing" if not state["error"] else "parent_pc_startup_failed",
                    **state,
                }, [(b"retry-after", b"5")])
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1013})


app = BootstrapServer()
