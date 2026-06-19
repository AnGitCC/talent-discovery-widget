"""Starlette server: WebSocket for chat, HTTP for static widget files + exports."""
import json
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent
_project_dir = _backend_dir.parent
sys.path.insert(0, str(_project_dir))
sys.path.insert(0, str(_backend_dir))

from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.responses import FileResponse, JSONResponse, RedirectResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware

from backend.ws_manager import ws_manager
from backend.message_builder import stream_response
from backend.views import mtp_profile

WIDGET_DIR = str(_project_dir / "widget")
DEMO_DIR = str(_project_dir / "demo")


async def root(request):
    return RedirectResponse(url="/demo")


async def demo(request):
    return FileResponse(str(Path(DEMO_DIR) / "demo-hr-portal.html"))


async def health(request):
    return JSONResponse({"status": "ok"})


async def debug_status(request):
    import json
    from data.talent_store import get_store
    store = get_store()
    records = len(store.records) if store.records else 0
    loaded = store.df is not None and len(store.df) > 0
    xlsx = _project_dir / "test_talent_data_400_cn.xlsx"
    return JSONResponse({
        "records": records,
        "loaded": loaded,
        "xlsx_exists": xlsx.exists(),
        "xlsx_path": str(xlsx),
        "cwd_files": [str(p.name) for p in _project_dir.glob("*.xlsx")],
    })


async def export_excel(request):
    from backend.utils.export import export_candidates_excel
    session_id = request.path_params.get("session_id", "")
    ctx = ws_manager.get(session_id)
    if not ctx or not ctx.cached_candidates:
        return JSONResponse({"error": "No data to export"}, status_code=404)
    filepath = export_candidates_excel(ctx.cached_candidates)
    return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    session_id = ws.path_params.get("session_id", "default")
    ctx = ws_manager.get_or_create(session_id)

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            if msg_type == "message":
                user_text = msg.get("text", "")
                ctx.add_message("user", user_text)
                ctx.last_query = user_text
                async for ws_msg in stream_response(ctx, user_text):
                    await ws.send_json(ws_msg)

            elif msg_type == "action":
                action = msg.get("action", "")
                msg_ids = msg.get("ids", [])
                if action in ("compare", "report"):
                    user_text = ctx.last_query if action == "compare" else ""
                    async for ws_msg in stream_response(ctx, user_text, action=action, ids=msg_ids):
                        await ws.send_json(ws_msg)
                elif action == "export":
                    await ws.send_json({"type": "text", "content": f"Download: /api/export/{ctx.session_id}"})
                    await ws.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "content": str(e)})
            await ws.send_json({"type": "done"})
        except Exception:
            pass


async def architecture(request):
    return FileResponse(str(Path(DEMO_DIR) / "architecture.html"))


async def pdf_export(request):
    """Convert posted HTML to PDF and return as download."""
    import json
    import traceback
    body = await request.body()
    data = json.loads(body)
    html_content = data.get("html", "")
    filename = data.get("filename", "人才报告")
    try:
        from weasyprint import HTML
        import asyncio
        def _render(): return HTML(string=html_content).write_pdf()
        pdf_bytes = await asyncio.to_thread(_render)
    except Exception as e:
        print(f"[PDF] FAILED: {e}")
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
    from urllib.parse import quote
    safe_fn = quote(filename)
    return Response(pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_fn}.pdf"})


routes = [
    Route("/", root),
    Mount("/widget", app=StaticFiles(directory=WIDGET_DIR)),
    Route("/demo", demo),
    Mount("/demo/static", app=StaticFiles(directory=DEMO_DIR)),
    Route("/mtp/{eid}", mtp_profile),
    Route("/architecture", architecture),
    Route("/api/health", health),
    Route("/api/debug", debug_status),
    Route("/api/export/{session_id}", export_excel),
    WebSocketRoute("/ws/{session_id}", ws_endpoint),
]

app = Starlette(routes=routes)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Eager-load talent data at startup ──
from data.talent_store import get_store
_store = get_store()
try:
    _store.load(embedding_fn=None)
    print(f"✓ Loaded {len(_store.records)} talent records at startup")
except Exception as e:
    print(f"✗ Failed to load talent data: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
