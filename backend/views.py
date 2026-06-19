"""MTP talent profile view — injects employee data into standalone HTML template."""
import json, sys, traceback
from pathlib import Path
from starlette.responses import HTMLResponse, JSONResponse

async def mtp_profile(request):
    eid = request.path_params.get("eid", "")
    if not eid:
        return HTMLResponse("<h2>Missing employee ID</h2>", status_code=400)

    try:
        import numpy as np
        # Use same path resolution as server.py
        backend_dir = Path(__file__).resolve().parent
        project_dir = backend_dir.parent
        sys.path.insert(0, str(project_dir))
        sys.path.insert(0, str(backend_dir))

        from data.talent_store import get_store
        store = get_store()
        if store.df is None or len(store.records) == 0:
            store.load(embedding_fn=None)

        profile = store.get_by_id(eid)
        if not profile:
            return HTMLResponse(f"<h2>Employee {eid} not found</h2>", status_code=404)

        data = {}
        for k, v in dict(profile).items():
            if v is None: continue
            if isinstance(v, (np.integer,)): data[k] = int(v)
            elif isinstance(v, (np.floating,)): data[k] = float(v)
            elif isinstance(v, (np.bool_,)): data[k] = bool(v)
            else: data[k] = v
        data["id"] = eid

        g = str(data.get("性别", ""))
        pool = "f" if g == "女" else "m"
        count = 91 if pool == "f" else 64
        h = 0
        for ch in str(eid):
            h = ((h << 5) - h) + ord(ch)
            h |= 0
        data["avatar"] = f"/widget/avatars/avatar-{pool}-{(abs(h) % count) + 1:03d}.png"
        data["history"] = {}

        # Use project_dir for template path
        template_path = project_dir / "demo" / "mtp-v3.html"
        template = template_path.read_text(encoding="utf-8")
        ds = template.find("var D={")
        de = template.find("(function(){", ds)
        if de < 0:
            de = len(template)
        json_data = json.dumps(data, ensure_ascii=False, default=str)
        injected = (
            template[:ds]
            + "var D=" + json_data
            + ';\nD.id="' + eid + '";\nD.history=D.history||{};\nD.avatar="' + data["avatar"] + '";\n'
            + template[de:]
        )
        return HTMLResponse(injected)

    except Exception as exc:
        traceback.print_exc()
        return HTMLResponse(f"<h2>Error loading profile: {exc}</h2>", status_code=500)
