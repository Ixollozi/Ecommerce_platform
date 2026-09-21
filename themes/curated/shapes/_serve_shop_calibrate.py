"""Shop overlay calibrator — place 3 product tiles + catalog CTA on C-dark-bottom.

Open http://127.0.0.1:8768/shop-calibrate.html
Toggle Desktop / Mobile, drag & resize, Save → inbox/shop_slots.json
Then say «готово» in chat.
"""
from __future__ import annotations

import json
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
PATHS = OUT / "paths"
INBOX = OUT / "inbox"
APPROVED = OUT / "approved"
PORT = 8768

DESK_ART = [1024.0, 828.0]
MOB_ART = [390.0, 844.0]

SLOT_IDS = ("product-1", "product-2", "product-3", "catalog-cta")

DEFAULT_DESK = {
    "product-1": [520.0, 470.0, 100.0, 100.0],
    "product-2": [640.0, 455.0, 100.0, 100.0],
    "product-3": [760.0, 475.0, 100.0, 100.0],
    "catalog-cta": [560.0, 600.0, 220.0, 42.0],
}

DEFAULT_MOB = {
    "product-1": [36.0, 700.0, 72.0, 72.0],
    "product-2": [130.0, 712.0, 72.0, 72.0],
    "product-3": [224.0, 704.0, 72.0, 72.0],
    "catalog-cta": [70.0, 792.0, 200.0, 36.0],
}

# Desktop path paint order for backdrop
DESK_SHAPES = ("C-dark-upper", "C-dark-bottom")

# Mobile C transforms — match current approved mobile pack
MOB_C_BBOX = {
    "C-dark-upper": (400.0, 327.5, 624.0, 297.09),
    "C-dark-bottom": (388.0, 389.0, 636.0, 236.0),
}


def path_d(name: str) -> str:
    text = (PATHS / f"{name}.svg").read_text(encoding="utf-8")
    m = re.search(r'\bd="([^"]+)"', text)
    if not m:
        raise SystemExit(f"no path in {name}.svg")
    return " ".join(m.group(1).split())


# Paths that bleed past artboard fold on desktop / mobile pack
PATH_BLEED_YMAX = {
    "C-dark-bottom": 826.0,
}


def fit_slot(bbox, slot):
    bx, by, bw, bh = bbox
    sx, sy, sw, sh = slot
    scale = min(sw / bw, sh / bh)
    tw, th = bw * scale, bh * scale
    tx = sx + (sw - tw) / 2 - bx * scale
    ty = sy + (sh - th) / 2 - by * scale
    return scale, tx, ty


def mob_focus_view(mob_transforms: dict, mob_c_slots: dict) -> list[float]:
    """Crop around full C figure (incl. rounded bleed) so calibrator can edit."""
    tops = []
    bottoms = []
    lefts = []
    rights = []
    for sid, slot in mob_c_slots.items():
        x, y, w, h = slot
        lefts.append(x)
        tops.append(y)
        rights.append(x + w)
        bottoms.append(y + h)
        t = mob_transforms[sid]
        ymax = PATH_BLEED_YMAX.get(sid)
        if ymax is not None:
            bottoms.append(t["ty"] + ymax * t["scale"])
    pad = 36.0
    x0 = min(lefts) - pad
    y0 = min(tops) - pad
    x1 = max(rights) + pad
    y1 = max(bottoms) + pad
    # Keep readable square-ish crop, at least 420 tall
    w = max(420.0, x1 - x0)
    h = max(420.0, y1 - y0)
    return [round(x0, 1), round(y0, 1), round(w, 1), round(h, 1)]


def desk_focus_view() -> list[float]:
    """Crop desktop artboard to C-dark lobe (full rounded bottom)."""
    # Path roughly x 388–1024, y 327–826
    return [360.0, 300.0, 680.0, 540.0]


def load_mobile_c_slots() -> dict:
    for path in (INBOX / "mobile_slots.json", APPROVED / "mobile_slots.json"):
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        slots = data.get("slots") or {}
        out = {}
        for k in ("C-dark-upper", "C-dark-bottom"):
            if k in slots and len(slots[k]) >= 4:
                out[k] = [float(x) for x in slots[k][:4]]
        if len(out) == 2:
            return out
    return {
        "C-dark-upper": [-41.36, 630.84, 449.09, 213.81],
        "C-dark-bottom": [-50.91, 679.55, 470.0, 174.4],
    }


def load_shop() -> dict:
    for path in (INBOX / "shop_slots.json", APPROVED / "shop_slots.json"):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}


def normalize_mode(raw: dict | None, art: list[float], defaults: dict) -> dict:
    slots = dict(defaults)
    if isinstance(raw, dict):
        src = raw.get("slots") if isinstance(raw.get("slots"), dict) else raw
        for sid in SLOT_IDS:
            v = src.get(sid) if isinstance(src, dict) else None
            if isinstance(v, (list, tuple)) and len(v) >= 4:
                slots[sid] = [float(v[0]), float(v[1]), float(v[2]), float(v[3])]
    return {"art": list(art), "slots": slots}


def build_payload() -> dict:
    existing = load_shop()
    mob_c = load_mobile_c_slots()
    mob_transforms = {}
    for sid, slot in mob_c.items():
        scale, tx, ty = fit_slot(MOB_C_BBOX[sid], slot)
        mob_transforms[sid] = {
            "scale": round(scale, 6),
            "tx": round(tx, 3),
            "ty": round(ty, 3),
            "slot": slot,
        }

    return {
        "desk": normalize_mode(existing.get("desk"), DESK_ART, DEFAULT_DESK),
        "mob": normalize_mode(existing.get("mob"), MOB_ART, DEFAULT_MOB),
        "paths": {sid: path_d(sid) for sid in DESK_SHAPES},
        "fills": {"C-dark-upper": "#c5b39d", "C-dark-bottom": "#2a2c2b"},
        "mob_transforms": mob_transforms,
        "desk_view": desk_focus_view(),
        "mob_view": mob_focus_view(mob_transforms, mob_c),
        "labels": {
            "product-1": "Product 1",
            "product-2": "Product 2",
            "product-3": "Product 3",
            "catalog-cta": "View Catalog",
        },
        "slot_ids": list(SLOT_IDS),
    }


def build_html() -> str:
    payload = build_payload()
    data_json = json.dumps(payload, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Curated — shop slots calibrate</title>
<style>
:root {{ color-scheme: dark; --cream: #f3efe7; --accent: #c5b39d; --ink: #2a2c2b; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; min-height: 100svh; font-family: system-ui, sans-serif;
  background: #141514; color: #eee; display: grid;
  grid-template-columns: minmax(240px, 300px) 1fr; gap: 0;
}}
aside {{
  padding: 1.1rem 1rem 1.4rem; border-right: 1px solid #2c2d2c;
  display: flex; flex-direction: column; gap: 0.85rem; overflow: auto;
}}
h1 {{ margin: 0; font-size: 1rem; letter-spacing: 0.04em; }}
p, li {{ margin: 0; font-size: 0.8rem; line-height: 1.45; color: #b5b3ad; }}
ol {{ margin: 0; padding-left: 1.1rem; display: grid; gap: 0.35rem; }}
code {{ color: #c5b39d; font-size: 0.75rem; }}
.btns {{ display: flex; flex-wrap: wrap; gap: 0.45rem; }}
.mode {{ display: flex; gap: 0.35rem; }}
.mode button.active {{ outline: 2px solid var(--accent); }}
button {{
  appearance: none; border: 1px solid #3a3b3a; background: #222322; color: #eee;
  border-radius: 8px; padding: 0.55rem 0.75rem; font-size: 0.78rem; cursor: pointer;
}}
button.primary {{ background: linear-gradient(160deg,#d7c7b1,#9e8b72); color: #1e1f1e; border: 0; font-weight: 600; }}
button:hover {{ filter: brightness(1.08); }}
.status {{ font-size: 0.75rem; min-height: 1.2em; color: #8fd18f; }}
.status.err {{ color: #f0a0a0; }}
.list {{ display: grid; gap: 0.35rem; }}
.list button {{
  text-align: left; display: flex; justify-content: space-between; gap: 0.5rem;
}}
.list button.active {{ outline: 2px solid var(--accent); }}
.hint {{ font-size: 0.72rem; color: #888; }}
main {{
  display: grid; place-items: center; padding: 1.25rem; overflow: auto;
}}
.stage-wrap {{
  position: relative; overflow: hidden; border: 3px solid #3a3b3a;
  box-shadow: 0 24px 64px rgba(0,0,0,.45); background: var(--cream);
  touch-action: none; user-select: none;
}}
.stage-wrap.is-desk {{
  width: min(920px, 94vw);
  aspect-ratio: 680 / 540;
  border-radius: 12px;
}}
.stage-wrap.is-mob {{
  width: min(560px, 94vw);
  aspect-ratio: 1 / 1;
  border-radius: 16px;
}}
.stage-wrap svg.stage {{ display: block; width: 100%; height: 100%; }}
.hint-view {{
  font-size: 0.72rem; color: #9a968e; margin-top: -0.35rem;
}}
.handles {{ position: absolute; inset: 0; pointer-events: none; }}
.box {{
  position: absolute; border: 1.5px dashed transparent; pointer-events: auto;
  cursor: grab; background: rgba(245,240,230,0.18);
}}
.box.product {{ border-radius: 4px; }}
.box.cta {{ border-radius: 999px; background: rgba(197,179,157,0.55); }}
.box.active {{ border-color: #c44; background: rgba(196,68,68,0.12); }}
.box .tag {{
  position: absolute; left: 4px; top: 4px; font-size: 10px; font-weight: 700;
  color: #5a4038; background: rgba(255,255,255,.78); padding: 1px 5px; border-radius: 4px;
  pointer-events: none; letter-spacing: 0.03em; white-space: nowrap;
}}
.box .handle {{
  position: absolute; right: -7px; bottom: -7px; width: 14px; height: 14px;
  border-radius: 3px; background: #c44; border: 2px solid #fff; cursor: nwse-resize;
  pointer-events: auto;
}}
@media (max-width: 860px) {{
  body {{ grid-template-columns: 1fr; }}
  aside {{ border-right: 0; border-bottom: 1px solid #2c2d2c; }}
}}
</style>
</head>
<body>
<aside>
  <h1>SHOP · слоты в фигуре</h1>
  <p>3 квадрата товаров + кнопка каталога поверх <code>C-dark-bottom</code>.</p>
  <div class="mode">
    <button type="button" class="active" data-mode="desk" id="btn-desk">Desktop</button>
    <button type="button" data-mode="mob" id="btn-mob">Mobile</button>
  </div>
  <ol>
    <li>Расставь на Desktop → Save</li>
    <li>Переключи Mobile → расставь → Save</li>
    <li>В чат: <code>готово</code></li>
  </ol>
  <div class="btns">
    <button class="primary" id="btn-save" type="button">Сохранить</button>
    <button id="btn-download" type="button">Скачать JSON</button>
    <button id="btn-reset" type="button">Сброс режима</button>
  </div>
  <div class="status" id="status"></div>
  <p class="hint">Продукты — квадрат (aspect 1:1). CTA — свободный размер.</p>
  <p class="hint-view" id="hint-view">Кадр приближен к полной нижней фигуре (не весь экран телефона).</p>
  <p class="hint">Файл: <code>inbox/shop_slots.json</code></p>
  <div class="list" id="list"></div>
</aside>
<main>
  <div class="stage-wrap is-desk" id="frame">
    <svg class="stage" id="stage" viewBox="0 0 1024 828" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none"></svg>
    <div class="handles" id="handles"></div>
  </div>
</main>
<script>
const DATA = {data_json};

const frame = document.getElementById('frame');
const stage = document.getElementById('stage');
const handles = document.getElementById('handles');
const list = document.getElementById('list');
const statusEl = document.getElementById('status');

const state = {{
  mode: 'desk',
  desk: structuredClone(DATA.desk),
  mob: structuredClone(DATA.mob),
  active: 'product-1',
}};

function cur() {{ return state[state.mode]; }}
function art() {{ return cur().art; }}

function viewBox() {{
  // Focus crop so the full C figure (rounded bottom) fills the frame
  const v = state.mode === 'desk' ? DATA.desk_view : DATA.mob_view;
  return {{ x: v[0], y: v[1], w: v[2], h: v[3] }};
}}

function setStatus(msg, err=false) {{
  statusEl.textContent = msg;
  statusEl.classList.toggle('err', err);
}}

function round(n) {{ return Math.round(n * 100) / 100; }}

function renderSvg() {{
  const [aw, ah] = art();
  const vb = viewBox();
  stage.setAttribute('viewBox', `${{vb.x}} ${{vb.y}} ${{vb.w}} ${{vb.h}}`);
  stage.setAttribute('preserveAspectRatio', 'xMidYMid meet');
  const parts = [];
  // Full art cream so crop edges stay cream
  parts.push(`<rect x="0" y="0" width="${{aw * 2}}" height="${{ah * 2}}" fill="#f3efe7"/>`);
  if (state.mode === 'desk') {{
    for (const id of ['C-dark-upper', 'C-dark-bottom']) {{
      parts.push(`<path fill="${{DATA.fills[id]}}" d="${{DATA.paths[id]}}"/>`);
    }}
  }} else {{
    for (const id of ['C-dark-upper', 'C-dark-bottom']) {{
      const t = DATA.mob_transforms[id];
      parts.push(`<g transform="translate(${{t.tx}} ${{t.ty}}) scale(${{t.scale}})"><path fill="${{DATA.fills[id]}}" d="${{DATA.paths[id]}}"/></g>`);
    }}
  }}
  const cta = cur().slots['catalog-cta'];
  if (cta) {{
    const [x,y,w,h] = cta;
    parts.push(`<rect x="${{x}}" y="${{y}}" width="${{w}}" height="${{h}}" rx="${{h/2}}" fill="#c5b39d" opacity="0.35"/>`);
    parts.push(`<text x="${{x + w/2}}" y="${{y + h*0.62}}" text-anchor="middle" fill="#f5f0e6" font-size="${{Math.max(9, h*0.35)}}" font-family="system-ui" letter-spacing="0.08em">VIEW CATALOG</text>`);
  }}
  stage.innerHTML = parts.join('');
}}

function frameScale() {{
  const rect = frame.getBoundingClientRect();
  const vb = viewBox();
  return {{
    sx: rect.width / vb.w,
    sy: rect.height / vb.h,
    ox: vb.x,
    oy: vb.y,
    rect,
  }};
}}

function renderHandles() {{
  handles.innerHTML = '';
  const {{ sx, sy, ox, oy }} = frameScale();
  for (const id of DATA.slot_ids) {{
    const [x, y, w, h] = cur().slots[id];
    const el = document.createElement('div');
    const isCta = id === 'catalog-cta';
    el.className = 'box ' + (isCta ? 'cta' : 'product') + (id === state.active ? ' active' : '');
    el.dataset.id = id;
    el.style.left = ((x - ox) * sx) + 'px';
    el.style.top = ((y - oy) * sy) + 'px';
    el.style.width = Math.max(10, w * sx) + 'px';
    el.style.height = Math.max(10, h * sy) + 'px';
    el.innerHTML = `<span class="tag">${{DATA.labels[id] || id}}</span><span class="handle"></span>`;
    handles.appendChild(el);
  }}
  [...list.querySelectorAll('button')].forEach(b => {{
    b.classList.toggle('active', b.dataset.id === state.active);
  }});
}}

function renderList() {{
  list.innerHTML = DATA.slot_ids.map(id => {{
    const [x,y,w,h] = cur().slots[id];
    return `<button type="button" data-id="${{id}}">
      <span>${{DATA.labels[id] || id}}</span>
      <code>${{Math.round(w)}}×${{Math.round(h)}}</code>
    </button>`;
  }}).join('');
}}

function setMode(mode) {{
  state.mode = mode;
  frame.classList.toggle('is-desk', mode === 'desk');
  frame.classList.toggle('is-mob', mode === 'mob');
  document.getElementById('btn-desk').classList.toggle('active', mode === 'desk');
  document.getElementById('btn-mob').classList.toggle('active', mode === 'mob');
  const hv = document.getElementById('hint-view');
  if (hv) {{
    hv.textContent = mode === 'desk'
      ? 'Desktop: кадр на всю нижнюю фигуру (с округлым низом).'
      : 'Mobile: крупный кроп нижней фигуры (не весь телефон).';
  }}
  renderList();
  renderSvg();
  renderHandles();
  setStatus(mode === 'desk' ? 'Режим Desktop — полная фигура' : 'Режим Mobile — полная фигура');
}}

function exportPayload() {{
  const pack = (mode) => {{
    const src = state[mode];
    const slots = {{}};
    for (const id of DATA.slot_ids) {{
      const [x,y,w,h] = src.slots[id];
      slots[id] = [round(x), round(y), round(w), round(h)];
    }}
    return {{ art: [...src.art], slots }};
  }};
  return {{
    desk: pack('desk'),
    mob: pack('mob'),
    saved_at: new Date().toISOString(),
  }};
}}

async function saveRemote() {{
  const payload = exportPayload();
  try {{
    const res = await fetch('/save-shop-slots', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(payload),
    }});
    if (!res.ok) throw new Error(await res.text());
    const j = await res.json();
    setStatus('Сохранено → ' + (j.path || 'inbox/shop_slots.json') + ' (' + state.mode + ')');
  }} catch (e) {{
    setStatus('Сервер недоступен — скачай JSON', true);
    downloadLocal();
  }}
}}

function downloadLocal() {{
  const payload = exportPayload();
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'shop_slots.json';
  a.click();
  URL.revokeObjectURL(a.href);
  setStatus('Скачан shop_slots.json — положи в inbox/');
}}

let drag = null;

handles.addEventListener('pointerdown', (e) => {{
  const box = e.target.closest('.box');
  if (!box) return;
  const id = box.dataset.id;
  state.active = id;
  const scaleMode = e.target.classList.contains('handle');
  const {{ sx, sy }} = frameScale();
  const [x, y, w, h] = cur().slots[id];
  drag = {{
    id, scaleMode,
    startX: e.clientX, startY: e.clientY,
    orig: [x, y, w, h],
    sx, sy,
  }};
  box.setPointerCapture?.(e.pointerId);
  e.preventDefault();
  renderList();
  renderHandles();
}});

window.addEventListener('pointermove', (e) => {{
  if (!drag) return;
  const dx = (e.clientX - drag.startX) / drag.sx;
  const dy = (e.clientY - drag.startY) / drag.sy;
  const [ox, oy, ow, oh] = drag.orig;
  const lockSquare = drag.id !== 'catalog-cta';
  if (drag.scaleMode) {{
    let nw = Math.max(28, ow + dx);
    let nh = lockSquare ? nw : Math.max(24, oh + dy);
    cur().slots[drag.id] = [ox, oy, nw, nh];
  }} else {{
    cur().slots[drag.id] = [ox + dx, oy + dy, ow, oh];
  }}
  renderSvg();
  renderHandles();
}});

window.addEventListener('pointerup', () => {{ drag = null; }});
window.addEventListener('pointercancel', () => {{ drag = null; }});

list.addEventListener('click', (e) => {{
  const b = e.target.closest('button[data-id]');
  if (!b) return;
  state.active = b.dataset.id;
  renderHandles();
}});

document.getElementById('btn-desk').onclick = () => setMode('desk');
document.getElementById('btn-mob').onclick = () => setMode('mob');
document.getElementById('btn-save').onclick = saveRemote;
document.getElementById('btn-download').onclick = downloadLocal;
document.getElementById('btn-reset').onclick = () => {{
  const src = state.mode === 'desk' ? DATA.desk : DATA.mob;
  state[state.mode] = structuredClone(src);
  renderList();
  renderSvg();
  renderHandles();
  setStatus('Сброшен режим ' + state.mode);
}};

window.addEventListener('resize', () => renderHandles());

setMode('desk');
</script>
</body>
</html>
"""


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUT), **kwargs)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def do_POST(self):
        if self.path.rstrip("/") != "/save-shop-slots":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            self.send_error(400, str(e))
            return
        INBOX.mkdir(parents=True, exist_ok=True)
        dest = INBOX / "shop_slots.json"
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        body = json.dumps({"ok": True, "path": str(dest).replace("\\", "/")}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/shop-calibrate.html", "/"):
            html = build_html()
            raw = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)
            return
        return super().do_GET()


def main() -> None:
    (OUT / "shop-calibrate.html").write_text(build_html(), encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Shop calibrate: http://127.0.0.1:{PORT}/shop-calibrate.html")
    print("Save writes inbox/shop_slots.json — then say «готово» in chat.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("bye")


if __name__ == "__main__":
    main()
