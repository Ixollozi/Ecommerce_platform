"""Generate + serve mobile shape calibrator.

Open http://127.0.0.1:8767/mobile-calibrate.html
Drag shapes, scale with corner handle, Save → inbox/mobile_slots.json
Then say «готово» in chat.
"""
from __future__ import annotations

import json
import re
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

OUT = Path(r"d:\Cursor\clothing_shop\themes\curated\shapes")
PATHS = OUT / "paths"
INBOX = OUT / "inbox"
PORT = 8767

MW, MH = 390.0, 844.0

BBOX = {
    "A-header-lower": (-1.0, -1.0, 471.0, 176.0),
    "A-dark-top-left": (0.0, 0.0, 422.0, 137.0),
    "C-dark-upper": (400.0, 327.5, 624.0, 297.09),
    "C-dark-bottom": (388.0, 389.0, 636.0, 236.0),
    "F-photo-left": (-1.33, 149.55, 290.08, 561.95),
    "G-photo-top": (551.64, -0.74, 284.36, 195.74),
    "H-photo-right": (744.0, 0.0, 280.05, 364.63),
    "G-photo-bottom": (185.4, 421.95, 246.86, 287.27),
}

FILLS = {
    "A-header-lower": "#baaa93",
    "A-dark-top-left": "#2a2c2b",
    "C-dark-upper": "#c5b39d",
    "C-dark-bottom": "#2a2c2b",
    "F-photo-left": "#c5b49f",
    "G-photo-top": "#d9c9b4",
    "H-photo-right": "#a8977f",
    "G-photo-bottom": "#8f7a60",
}

LABELS = {
    "A-dark-top-left": "A dark top",
    "A-header-lower": "A tan rim",
    "G-photo-top": "G photo top",
    "F-photo-left": "F photo L",
    "H-photo-right": "H photo R",
    "G-photo-bottom": "Q photo BL",
    "C-dark-upper": "C sm",
    "C-dark-bottom": "B dark bottom",
}

ORDER = (
    "A-header-lower",
    "A-dark-top-left",
    "C-dark-upper",   # C sm — under B
    "C-dark-bottom",  # B dark bottom — on top of C sm
    "F-photo-left",
    "G-photo-top",
    "H-photo-right",
    "G-photo-bottom",
)

# Default placed rects (from current frame pack)
DEFAULT_PLACED = {
    "A-header-lower": [-55.0, 60.66, 240.0, 89.68],
    "A-dark-top-left": [-18.0, 3.91, 210.0, 68.18],
    "C-dark-bottom": [-40.0, 687.8, 470.0, 174.4],
    "C-dark-upper": [195.0, 567.63, 220.0, 104.74],
    "F-photo-left": [-70.9, 150.0, 216.81, 420.0],
    "G-photo-top": [168.0, -13.54, 250.0, 172.09],
    "H-photo-right": [248.0, 226.1, 175.0, 227.9],
    "G-photo-bottom": [-27.9, 545.0, 184.8, 215.0],
}

COPY_SAFE = [52.0, 300.0, 286.0, 210.0]


def path_d(name: str) -> str:
    text = (PATHS / f"{name}.svg").read_text(encoding="utf-8")
    m = re.search(r'\bd="([^"]+)"', text)
    if not m:
        raise SystemExit(f"no path in {name}.svg")
    return " ".join(m.group(1).split())


def load_inbox() -> dict:
    inbox = INBOX / "mobile_slots.json"
    if inbox.exists():
        return json.loads(inbox.read_text(encoding="utf-8"))
    return {}


def load_placed() -> dict:
    data = load_inbox()
    if "slots" in data:
        return {k: list(v) for k, v in data["slots"].items()}
    if "placed" in data:
        return {k: list(v) for k, v in data["placed"].items()}
    layout = OUT / "mobile_layout.json"
    if layout.exists():
        layout_data = json.loads(layout.read_text(encoding="utf-8"))
        out = {}
        for k, v in layout_data.get("transforms", {}).items():
            if "placed" in v:
                out[k] = list(v["placed"])
        if out:
            return out
    return {k: list(v) for k, v in DEFAULT_PLACED.items()}


def load_order() -> list[str]:
    """Paint order back→front. Prefer inbox; else default (C sm under B)."""
    data = load_inbox()
    raw = data.get("order")
    if isinstance(raw, list) and raw:
        # keep known ids, append any missing from default
        seen = []
        for sid in raw:
            if sid in BBOX and sid not in seen:
                seen.append(sid)
        for sid in ORDER:
            if sid not in seen:
                seen.append(sid)
        return seen
    return list(ORDER)


def build_html() -> str:
    paths = {sid: path_d(sid) for sid in ORDER}
    placed = load_placed()
    # ensure every id has a placed rect
    for sid in ORDER:
        if sid not in placed:
            placed[sid] = list(DEFAULT_PLACED[sid])
    payload = {
        "phone": [MW, MH],
        "order": load_order(),
        "bbox": BBOX,
        "fills": FILLS,
        "labels": LABELS,
        "paths": paths,
        "placed": placed,
        "copy_safe": COPY_SAFE,
    }
    data_json = json.dumps(payload, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Curated — mobile calibrate</title>
<style>
:root {{ color-scheme: dark; --cream: #f3efe7; --ink: #1e1f1e; --accent: #c5b39d; }}
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
button {{
  appearance: none; border: 1px solid #3a3b3a; background: #222322; color: #eee;
  border-radius: 8px; padding: 0.55rem 0.75rem; font-size: 0.78rem; cursor: pointer;
}}
button.primary {{ background: linear-gradient(160deg,#d7c7b1,#9e8b72); color: #1e1f1e; border: 0; font-weight: 600; }}
button:hover {{ filter: brightness(1.08); }}
.status {{ font-size: 0.75rem; min-height: 1.2em; color: #8fd18f; }}
.status.err {{ color: #f0a0a0; }}
.list {{ display: grid; gap: 0.3rem; }}
.list .row {{
  display: grid; grid-template-columns: 1fr auto; gap: 0.3rem; align-items: stretch;
}}
.list .row > button.pick {{
  text-align: left; display: flex; justify-content: space-between; gap: 0.5rem;
}}
.list .row > button.pick.active {{ outline: 2px solid var(--accent); }}
.list .zbtns {{ display: flex; flex-direction: column; gap: 2px; }}
.list .zbtns button {{
  padding: 0.15rem 0.4rem; min-width: 1.6rem; font-size: 0.7rem; line-height: 1.1;
}}
.swatch {{ width: 12px; height: 12px; border-radius: 3px; flex: 0 0 auto; }}
.hint {{ font-size: 0.72rem; color: #888; }}
.hint code {{ font-size: 0.68rem; }}
p.hint-file {{ margin-top: -0.25rem; }}
main {{
  display: grid; place-items: center; padding: 1.25rem; overflow: auto;
}}
.phone-wrap {{
  position: relative; width: min(390px, 92vw);
  border-radius: 28px; overflow: hidden; border: 3px solid #3a3b3a;
  box-shadow: 0 24px 64px rgba(0,0,0,.45); background: var(--cream);
  touch-action: none; user-select: none;
}}
.phone-wrap svg.stage {{ display: block; width: 100%; height: auto; }}
.handles {{
  position: absolute; inset: 0; pointer-events: none;
}}
.box {{
  position: absolute; border: 1.5px dashed transparent; pointer-events: auto;
  cursor: grab;
}}
.box.active {{ border-color: #c44; background: rgba(196,68,68,0.06); }}
.box .tag {{
  position: absolute; left: 4px; top: 4px; font-size: 10px; font-weight: 700;
  color: #5a4038; background: rgba(255,255,255,.72); padding: 1px 5px; border-radius: 4px;
  pointer-events: none; letter-spacing: 0.03em;
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
  <h1>MOBILE · калибровка слотов</h1>
  <p>Тащи фигуру мышью. Угол справа-снизу — масштаб (пропорции path сохраняются).</p>
  <ol>
    <li>Расставь как нравится</li>
    <li>Жми <strong>Сохранить</strong></li>
    <li>В чат: <code>готово</code> — зафиксирую в коде</li>
  </ol>
  <div class="btns">
    <button class="primary" id="btn-save" type="button">Сохранить</button>
    <button id="btn-download" type="button">Скачать JSON</button>
    <button id="btn-reset" type="button">Сброс</button>
  </div>
  <div class="status" id="status"></div>
  <p class="hint">Список слоёв: сверху = спереди, ↓ = назад. ↑↓ меняют z-order. Позиции не трогают.</p>
  <p class="hint">Файл: <code>inbox/mobile_slots.json</code></p>
  <div class="list" id="list"></div>
</aside>
<main>
  <div class="phone-wrap" id="phone">
    <svg class="stage" id="stage" viewBox="0 0 {MW:g} {MH:g}" xmlns="http://www.w3.org/2000/svg"></svg>
    <div class="handles" id="handles"></div>
  </div>
</main>
<script>
const DATA = {data_json};

const phone = document.getElementById('phone');
const stage = document.getElementById('stage');
const handles = document.getElementById('handles');
const list = document.getElementById('list');
const statusEl = document.getElementById('status');

const state = {{
  placed: structuredClone(DATA.placed),
  order: [...DATA.order],
  active: DATA.order[0],
}};

function fitToPlaced(id) {{
  const [bx, by, bw, bh] = DATA.bbox[id];
  const [x, y, w, h] = state.placed[id];
  // keep AR from bbox; w drives scale
  const scale = w / bw;
  const hh = bh * scale;
  state.placed[id][3] = hh;
  const tx = x - bx * scale;
  const ty = y - by * scale;
  return {{ scale, tx, ty, x, y, w, h: hh }};
}}

function renderSvg() {{
  const parts = [];
  parts.push(`<rect width="{MW:g}" height="{MH:g}" fill="#f3efe7"/>`);
  const [cx, cy, cw, ch] = DATA.copy_safe;
  parts.push(`<rect x="${{cx}}" y="${{cy}}" width="${{cw}}" height="${{ch}}" fill="none" stroke="#c44" stroke-width="1.5" stroke-dasharray="6 5" opacity="0.7"/>`);
  parts.push(`<text x="{MW/2:g}" y="${{cy + 18}}" text-anchor="middle" fill="#c44" font-size="9" font-family="system-ui" letter-spacing="0.08em">COPY SAFE</text>`);
  for (const id of state.order) {{
    const t = fitToPlaced(id);
    const fill = DATA.fills[id];
    const op = id.includes('photo') ? 0.92 : 1;
    const d = DATA.paths[id];
    parts.push(`<g data-id="${{id}}" transform="translate(${{t.tx}} ${{t.ty}}) scale(${{t.scale}})"><path fill="${{fill}}" fill-opacity="${{op}}" d="${{d}}"/></g>`);
  }}
  // nav mock
  let nav = '';
  for (let i = 0; i < 6; i++) nav += `<circle cx="${{28 + i * 28}}" cy="36" r="10" fill="#c5b49f"/>`;
  parts.push(`<g>${{nav}}</g>`);
  parts.push(`<text x="{MW/2:g}" y="420" text-anchor="middle" fill="#1e1f1e" font-family="Georgia,serif" font-size="20" letter-spacing="0.1em">CURATED FOR</text>`);
  parts.push(`<text x="{MW/2:g}" y="448" text-anchor="middle" fill="#1e1f1e" font-family="Georgia,serif" font-size="20" letter-spacing="0.1em">THE DISCERNING</text>`);
  stage.innerHTML = parts.join('');
}}

function phoneScale() {{
  const rect = phone.getBoundingClientRect();
  return {{ sx: rect.width / DATA.phone[0], sy: rect.height / DATA.phone[1], rect }};
}}

function renderHandles() {{
  handles.innerHTML = '';
  const {{ sx, sy }} = phoneScale();
  for (const id of state.order) {{
    fitToPlaced(id);
    const [x, y, w, h] = state.placed[id];
    const el = document.createElement('div');
    el.className = 'box' + (id === state.active ? ' active' : '');
    el.dataset.id = id;
    el.style.left = (x * sx) + 'px';
    el.style.top = (y * sy) + 'px';
    el.style.width = Math.max(8, w * sx) + 'px';
    el.style.height = Math.max(8, h * sy) + 'px';
    el.style.zIndex = String(10 + state.order.indexOf(id));
    el.innerHTML = `<span class="tag">${{DATA.labels[id] || id}}</span><span class="handle" data-scale="1"></span>`;
    handles.appendChild(el);
  }}
  [...list.querySelectorAll('button.pick')].forEach(b => {{
    b.classList.toggle('active', b.dataset.id === state.active);
  }});
}}

function moveLayer(id, dir) {{
  // dir -1 = toward back (earlier in paint order), +1 = toward front
  const i = state.order.indexOf(id);
  if (i < 0) return;
  const j = i + dir;
  if (j < 0 || j >= state.order.length) return;
  const next = state.order.slice();
  [next[i], next[j]] = [next[j], next[i]];
  state.order = next;
  state.active = id;
  renderList();
  renderSvg();
  renderHandles();
  setStatus((DATA.labels[id] || id) + (dir < 0 ? ' → назад' : ' → вперёд'));
}}

function renderList() {{
  // Show front→back in UI (top of list = front), opposite of paint order
  const frontFirst = [...state.order].reverse();
  list.innerHTML = frontFirst.map((id, visIdx) => {{
    const lab = DATA.labels[id] || id;
    const fill = DATA.fills[id];
    const paintIdx = state.order.indexOf(id);
    const canBack = paintIdx > 0;
    const canFront = paintIdx < state.order.length - 1;
    return `<div class="row" data-id="${{id}}">
      <button type="button" class="pick" data-id="${{id}}">
        <span style="display:flex;align-items:center;gap:.45rem">
          <span class="swatch" style="background:${{fill}}"></span>${{lab}}
        </span>
        <code>z${{state.order.length - paintIdx}}</code>
      </button>
      <div class="zbtns">
        <button type="button" data-z="front" data-id="${{id}}" title="Вперёд (выше)" ${{canFront ? '' : 'disabled'}}>↑</button>
        <button type="button" data-z="back" data-id="${{id}}" title="Назад (ниже)" ${{canBack ? '' : 'disabled'}}>↓</button>
      </div>
    </div>`;
  }}).join('');
}}

function setStatus(msg, err=false) {{
  statusEl.textContent = msg;
  statusEl.classList.toggle('err', err);
}}

function exportPayload() {{
  const slots = {{}};
  for (const id of state.order) {{
    fitToPlaced(id);
    const [x, y, w, h] = state.placed[id];
    slots[id] = [round(x), round(y), round(w), round(h)];
  }}
  // also keep any placed ids not in order
  for (const id of Object.keys(state.placed)) {{
    if (!(id in slots)) {{
      fitToPlaced(id);
      const [x, y, w, h] = state.placed[id];
      slots[id] = [round(x), round(y), round(w), round(h)];
    }}
  }}
  return {{
    mode: 'frame',
    phone: DATA.phone,
    copy_safe: DATA.copy_safe,
    order: [...state.order],
    slots,
    labels: DATA.labels,
    saved_at: new Date().toISOString(),
  }};
}}

function round(n) {{ return Math.round(n * 100) / 100; }}

async function saveRemote() {{
  const payload = exportPayload();
  try {{
    const res = await fetch('/save-mobile-slots', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(payload),
    }});
    if (!res.ok) throw new Error(await res.text());
    const j = await res.json();
    setStatus('Сохранено → ' + (j.path || 'inbox/mobile_slots.json'));
  }} catch (e) {{
    setStatus('Сервер недоступен — скачай JSON вручную', true);
    downloadLocal();
  }}
}}

function downloadLocal() {{
  const payload = exportPayload();
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'mobile_slots.json';
  a.click();
  URL.revokeObjectURL(a.href);
  setStatus('Скачан mobile_slots.json — положи в inbox/');
}}

// interactions
let drag = null;

handles.addEventListener('pointerdown', (e) => {{
  const box = e.target.closest('.box');
  if (!box) return;
  const id = box.dataset.id;
  state.active = id;
  const scaleMode = e.target.classList.contains('handle');
  const {{ sx, sy, rect }} = phoneScale();
  fitToPlaced(id);
  const [x, y, w, h] = state.placed[id];
  drag = {{
    id, scaleMode,
    startX: e.clientX, startY: e.clientY,
    orig: [x, y, w, h],
    sx, sy,
    pointerId: e.pointerId,
  }};
  box.setPointerCapture?.(e.pointerId);
  e.preventDefault();
  renderHandles();
}});

window.addEventListener('pointermove', (e) => {{
  if (!drag) return;
  const dx = (e.clientX - drag.startX) / drag.sx;
  const dy = (e.clientY - drag.startY) / drag.sy;
  const [ox, oy, ow, oh] = drag.orig;
  const [bx, by, bw, bh] = DATA.bbox[drag.id];
  const ar = bw / bh;
  if (drag.scaleMode) {{
    let nw = Math.max(40, ow + dx);
    let nh = nw / ar;
    state.placed[drag.id] = [ox, oy, nw, nh];
  }} else {{
    state.placed[drag.id] = [ox + dx, oy + dy, ow, oh];
  }}
  renderSvg();
  renderHandles();
}});

window.addEventListener('pointerup', () => {{ drag = null; }});
window.addEventListener('pointercancel', () => {{ drag = null; }});

list.addEventListener('click', (e) => {{
  const z = e.target.closest('button[data-z]');
  if (z) {{
    e.preventDefault();
    moveLayer(z.dataset.id, z.dataset.z === 'front' ? 1 : -1);
    return;
  }}
  const b = e.target.closest('button.pick[data-id]');
  if (!b) return;
  state.active = b.dataset.id;
  renderHandles();
}});

document.getElementById('btn-save').onclick = saveRemote;
document.getElementById('btn-download').onclick = downloadLocal;
document.getElementById('btn-reset').onclick = () => {{
  state.placed = structuredClone(DATA.placed);
  state.order = [...DATA.order];
  renderList();
  renderSvg();
  renderHandles();
  setStatus('Сброшено к стартовым слотам и слоям');
}};

window.addEventListener('resize', () => renderHandles());

renderList();
renderSvg();
renderHandles();
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
        if self.path.rstrip("/") != "/save-mobile-slots":
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
        dest = INBOX / "mobile_slots.json"
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        body = json.dumps({"ok": True, "path": str(dest).replace("\\\\", "/")}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/mobile-calibrate.html", "/"):
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
    # Also write a static snapshot for offline open (save won't work without server)
    (OUT / "mobile-calibrate.html").write_text(build_html(), encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Mobile calibrate: http://127.0.0.1:{PORT}/mobile-calibrate.html")
    print("Save writes inbox/mobile_slots.json — then say «готово» in chat.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("bye")


if __name__ == "__main__":
    main()
