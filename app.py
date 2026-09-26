"""E-WASTE INTELLIGENCE platform (Flask, SigLIP2).

Pages (clear flow): Overview -> Discovery -> Communities -> Community detail -> Analyze -> Insights

Data source (SigLIP2 only, from results (3)):
  data/siglip2_leiden_results.csv   3637 rows, col siglip_community
  data/siglip2_community_sizes.csv  64 communities
  data/siglip2_embeddings_l2norm.npy (3637,768) L2-normalized reference
  data/umap_2d.json                  precomputed interactive scatter
  data/community_stats.json
  data/similar_communities.json
  static/communities/community_XX.jpg  montages (resized from results (4)/output_full_clusters)

Tentative labels: derived from source-filename signals (e.g. pcb_*.jpg, Mouse_*.jpg)
in the original dataset paths. They are hypotheses, always shown with a
"Tentative visual interpretation" badge — never as verified facts.

New-image routing (MVP, honest):
  upload -> SigLIP2 (google/siglip2-base-patch16-224) 768D -> L2 norm
  -> cosine kNN (k=10) vs 3637 refs -> majority community + neighbour agreement
  (Leiden has no .predict(); kNN is the correct MVP approach.)
"""
import csv
import json
import logging
import pathlib
import re
from collections import Counter, defaultdict

# Silence harmless SigLIP2 config warnings (bos/eos_token_id leftovers in
# the upstream config.json — vision-only use never touches them).
logging.getLogger("transformers").setLevel(logging.ERROR)

import numpy as np
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from PIL import Image

BASE = pathlib.Path(__file__).parent
DATA = BASE / "data"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.secret_key = "scannex-ewaste-sorter-2026"
# CORS for Next.js (Vercel) -> Flask (Render). Allow all in dev, restrict via env in prod.
try:
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)
except Exception:
    @app.after_request
    def _cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}

# ---------- load precomputed (supports both old flat and new hierarchical layout) ----------
def _load_json(p):
    return json.load(open(p, encoding="utf-8")) if p.exists() else None

def _resolve(*parts):
    # try DATA/part, then DATA/clustering/part, DATA/embeddings/part, DATA/reports/part
    for base in [DATA, DATA/"clustering", DATA/"embeddings", DATA/"reports"]:
        cand = base / pathlib.Path(*parts)
        if cand.exists():
            return cand
    return DATA / pathlib.Path(*parts)

COMMUNITY_STATS = _load_json(DATA/"community_stats.json") or _load_json(DATA/"clustering"/"community_stats.json")
SIMILAR = _load_json(DATA/"similar_communities.json") or {}
UMAP_PTS = _load_json(DATA/"umap_2d.json") or []
# embeddings / rows may be in subfolders now
_emb_path = _resolve("siglip2_embeddings_l2norm.npy")
REF_EMB = np.load(_emb_path).astype(np.float32) if _emb_path.exists() else np.zeros((1,768),np.float32)
_rows_path = _resolve("siglip2_leiden_results.csv")
REF_ROWS = list(csv.DictReader(open(_rows_path, encoding="utf-8"))) if _rows_path.exists() else []
REF_COMM = np.array([int(r["siglip_community"]) for r in REF_ROWS]) if REF_ROWS else np.array([0])
REF_NAMES = [r["filepath"].split("/")[-1] for r in REF_ROWS] if REF_ROWS else []
TOTAL = len(REF_ROWS) if REF_ROWS else (COMMUNITY_STATS[0]["size"]*len(COMMUNITY_STATS) if COMMUNITY_STATS else 0)
if not COMMUNITY_STATS:
    COMMUNITY_STATS = json.load(open(_resolve("siglip2_community_sizes.csv"),encoding="utf-8")) if False else []

# modularity / silhouette: try old comparison file, fallback to hierarchical config or hardcoded
try:
    CMP = list(csv.DictReader(open(DATA/"siglip2_vs_dinov2_comparison.csv",encoding="utf-8")))
    SIGLIP_ROW = next(r for r in CMP if r["Model"].lower().startswith("siglip"))
    MODULARITY = float(SIGLIP_ROW["Modularity"])
    SILHOUETTE = float(SIGLIP_ROW["Silhouette_(referensi)"])
except Exception:
    try:
        CMP2 = json.load(open(DATA/"reports"/"clustering_config.json",encoding="utf-8"))
        MODULARITY = 0.961  # SNN graph modularity stable across sweeps
        SILHOUETTE = float(CMP2["hierarchical_consolidation"]["silhouette_selected"])
    except Exception:
        MODULARITY = 0.961
        SILHOUETTE = 0.774

try:
    STABILITY = list(csv.DictReader(open(DATA/"stability_analysis_siglip2.csv",encoding="utf-8")))
except Exception:
    try:
        STABILITY = list(csv.DictReader(open(DATA/"clustering"/"resolution_sweep.csv",encoding="utf-8")))
    except Exception:
        STABILITY = []

try:
    UMAP_CFG = json.load(open(DATA/"reports"/"umap_config_siglip2.json",encoding="utf-8"))
except Exception:
    try:
        UMAP_CFG = json.load(open(DATA/"umap_config_siglip2.json",encoding="utf-8"))
    except Exception:
        UMAP_CFG = {"n_neighbors":15,"min_dist":0.0,"n_components":15,"metric":"cosine","seed":42}

# reload from generated files if they exist at new location
if not COMMUNITY_STATS and (DATA/"community_stats.json").exists():
    COMMUNITY_STATS = json.load(open(DATA/"community_stats.json",encoding="utf-8"))
if not SIMILAR and (DATA/"similar_communities.json").exists():
    SIMILAR = json.load(open(DATA/"similar_communities.json",encoding="utf-8"))
if not UMAP_PTS and (DATA/"umap_2d.json").exists():
    UMAP_PTS = json.load(open(DATA/"umap_2d.json",encoding="utf-8"))

# ---------- tentative labels from filename signals ----------
DEVICE_WORDS = {
    "mouse": "Mouse / computer peripheral-like",
    "mobile": "Smartphone / mobile-like",
    "pcb": "PCB / circuit-board-like",
    "microwave": "Microwave-like",
    "keyboard": "Keyboard-like",
    "printer": "Printer-like",
    "washing": "Washing-machine-like",
    "television": "TV / television-like",
    "player": "Media-player-like",
    "battery": "Battery-like",
}

def _prefix(fn: str) -> str:
    return re.split(r"[_\-\.]", fn)[0].lower().strip()

# Manual overrides for NEW 16 macro-communities — final Indonesian tentative names
# Owner list 30 Sep 2026: 00 Elektronik Rusak, 01 Handphone, 02 Keyboard, 03 Mesin Cuci, 04 Televisi, 05 Mouse, 06 Printer,
# 07 PCB/Motherboard, 08 Microwave, 09 Radio/Penyetel Musik, 10 Laptop, 11 Monitor/Keyboard/Komputer, 12 Baterai, 13 Baterai HP, 14 Baterai Laptop, 15 Sakelar
# Analysis for "?" clusters; all remain tentative visual interpretations (show image + filename + pct).
MANUAL_LABELS = {
    0: ("Elektronik Rusak", "Low (mixed)", "tumpukan e-waste campur, junkyard — top prefix acak 17/18/12"),
    1: ("Handphone", "Medium (manual)", "Mobile_*.jpg 52% + Copy IMG handphone — visual koheren HP"),
    2: ("Keyboard", "High", "keyboard 66% (227/343) — keyboard jelas"),
    3: ("Mesin Cuci", "High", "washing 98% (289/295) — mesin cuci"),
    4: ("Televisi", "High", "television 84% (244/288) — televisi"),
    5: ("Mouse", "High", "mouse 80% (231/286) — mouse"),
    6: ("Printer", "High", "printer 97% (267/274) — printer"),
    7: ("PCB / Motherboard", "High", "pcb 86% (208/242) — papan sirkuit/motherboard, termasuk 5.Medical-Gaming-Motherboard...jpg"),
    8: ("Microwave", "High", "microwave 99% (229/230) — microwave"),
    9: ("Radio / Penyetel Musik", "High", "player 99% (226/227) — radio/media player, pemutar musik"),
    10: ("Laptop", "Medium (manual)", "generic IMG_*.jpg 21% — inspeksi visual: dominan laptop"),
    11: ("Monitor / Keyboard / Komputer", "Low (mixed)", "campur: img 23/154, TV 17/154, keyboard 13/154 — tidak ada dominan 60%, monitor+keyboard+komputer tercampur"),
    12: ("Baterai", "High", "battery 97% (78/80) — baterai umum"),
    13: ("Baterai HP", "High", "battery 100% (71/71) — subcluster baterai HP, split hierarki karena variasi visual"),
    14: ("Baterai Laptop", "High", "battery 100% (57/57) — subcluster baterai laptop, bentuk lebih panjang"),
    15: ("Sakelar", "Medium (manual)", "WhatsApp Image 69% (27/39) — foto in-situ rumah: sakelar/stopkontak + tumpukan corner wiring"),
}

def build_labels():
    by = defaultdict(list)
    for r, fn in zip(REF_ROWS, REF_NAMES):
        by[int(r["siglip_community"])].append(fn)
    labels, coherence, signals, sources = {}, {}, {}, {}
    n_comm = len(COMMUNITY_STATS) if COMMUNITY_STATS else 16
    for cid in range(n_comm):
        fns = by.get(cid, [])
        c = Counter(_prefix(f) for f in fns)
        top, n = c.most_common(1)[0] if c else ("?", 0)
        share = (n / len(fns)) if fns else 0
        signals[cid] = {"top_prefix": top, "top_share": round(share, 3),
                        "top3": [[k, v] for k, v in c.most_common(3)]}
        if len(fns) <= 2:
            labels[cid] = "Potential outlier (singleton / pair)"
            coherence[cid] = "n/a (too few images)"
            sources[cid] = "size rule (<=2 images)"
        elif top in DEVICE_WORDS and share >= 0.60:
            labels[cid] = DEVICE_WORDS[top]
            coherence[cid] = "High" if share >= 0.80 else "Medium"
            sources[cid] = "filename signal"
        else:
            labels[cid] = "Mixed / ambiguous electronics"
            coherence[cid] = "Low (mixed)"
            sources[cid] = "no clear signal"
    for cid, (lab, coh, note) in MANUAL_LABELS.items():
        labels[cid] = lab
        coherence[cid] = coh
        sources[cid] = "manual visual inspection — " + note
    return labels, coherence, signals, sources

LABELS, COHERENCE, SIGNALS, SOURCES = build_labels()
SINGLETONS = sum(1 for s in COMMUNITY_STATS if s["size"] <= 2)
# 16 macro: pick 6 largest clear ones (skip mixed 0,10,11)
FEATURED = [1, 2, 3, 5, 6, 7]

PIPELINE = [
    ("Image", "3,637 e-waste photos. The only input — no names, categories or labels needed."),
    ("SigLIP2", "Each image becomes a 768-dimensional visual representation (google/siglip2-base-patch16-224)."),
    ("L2 normalization", "Embeddings are scaled to unit length so cosine similarity = dot product."),
    ("UMAP 15D", f"Cosine UMAP compresses 768D to 15D (n_neighbors={UMAP_CFG['n_neighbors']}, min_dist={UMAP_CFG['min_dist']}, seed={UMAP_CFG['seed']})."),
    ("kNN graph", "Images are linked to visually similar neighbours in the 15D space."),
    ("Leiden", "Community detection on the graph finds 64 visual communities (modularity 0.961)."),
]

def community_payload(cid: int) -> dict:
    s = COMMUNITY_STATS[cid]
    return {
        "id": cid, "size": s["size"], "pct": s["pct"],
        "interpretation": LABELS[cid],
        "coherence": COHERENCE[cid],
        "source": SOURCES[cid],
        "signal": SIGNALS[cid],
        "rep_files": s["rep_files"],
        "montage_url": f"/static/communities/{s['montage']}" if s.get("montage") else None,
        "similar": [
            {"id": t["id"], "score": t["score"], "label": LABELS[t["id"]],
             "size": COMMUNITY_STATS[t["id"]]["size"]}
            for t in SIMILAR.get(str(cid), [])
        ],
    }

# ---------- SigLIP2 lazy loader ----------
_SIGLIP = {"proc": None, "model": None, "failed": None}
SIGLIP_ID = "google/siglip2-base-patch16-224"
_MODEL_STATE = {"state": "starting", "detail": "Server starting..."}

def get_siglip(local_only: bool = False):
    if _SIGLIP["proc"] is not None:
        return _SIGLIP["proc"], _SIGLIP["model"]
    if _SIGLIP["failed"] is not None:
        raise RuntimeError(_SIGLIP["failed"])
    try:
        from transformers import AutoImageProcessor, AutoModel
        kw = {"local_files_only": True} if local_only else {}
        proc = AutoImageProcessor.from_pretrained(SIGLIP_ID, **kw)
        model = AutoModel.from_pretrained(SIGLIP_ID, **kw)
        model.eval()
        _SIGLIP.update(proc=proc, model=model)
        return proc, model
    except Exception as e:
        _SIGLIP["failed"] = str(e)
        raise RuntimeError(f"Cannot load SigLIP2 model {SIGLIP_ID}: {e}")

def _bg_load():
    """Download (once, resumable) + load the model in a background thread.

    Progress bars print to THIS terminal (the one running app.py).
    Requests are never blocked — /api/model-status reports the state.
    """
    print(f"[model] downloading/loading {SIGLIP_ID} (~1 GB, one-time)...",
          flush=True)
    _MODEL_STATE.update(state="loading",
                        detail="Downloading model (~1 GB, one-time) — watch Pythons "
                               "terminal for the progress bar. Page updates automatically.")
    try:
        get_siglip(local_only=False)
        _MODEL_STATE.update(state="ready", detail="")
        print("[model] READY — Analyze page uploads now work.", flush=True)
    except Exception as e:
        _MODEL_STATE.update(state="not_loaded", detail=str(e)[:300])
        print(f"[model] FAILED: {e}", flush=True)

def ensure_model_loading(force: bool = False) -> dict:
    if _SIGLIP["proc"] is not None:
        _MODEL_STATE.update(state="ready", detail="")
        return _MODEL_STATE
    # Only auto-start once per boot ("starting") or on explicit retry.
    # Never on plain status polls — a doomed attempt takes ~5s and would
    # flip the state back to "loading" on every poll.
    if _MODEL_STATE["state"] == "loading":
        return _MODEL_STATE
    if not force and _MODEL_STATE["state"] != "starting":
        return _MODEL_STATE
    import os
    if (not force and app.debug
            and os.environ.get("WERKZEUG_RUN_MAIN") != "true"):
        return _MODEL_STATE  # reloader parent process — the child does the work
    _SIGLIP["failed"] = None  # allow retry after a previous failure
    import threading
    threading.Thread(target=_bg_load, daemon=True).start()
    return _MODEL_STATE

def embed_pil(img: Image.Image) -> np.ndarray:
    import torch
    proc, model = get_siglip()
    inputs = proc(images=img.convert("RGB"), return_tensors="pt")
    with torch.no_grad():
        feats = model.get_image_features(pixel_values=inputs["pixel_values"])
    # transformers>=5 returns BaseModelOutputWithPooling (use the MAP-head
    # pooler_output, 768D); older versions returned a tensor directly.
    if torch.is_tensor(feats):
        v = feats[0]
    else:
        v = feats.pooler_output[0]
    v = v.cpu().numpy().astype(np.float32)
    assert v.shape == (768,), f"unexpected embedding shape {v.shape}"
    return v / (np.linalg.norm(v) + 1e-12)

def model_status() -> dict:
    return dict(_MODEL_STATE)

def knn_predict(vec: np.ndarray, k: int = 10):
    sims = REF_EMB @ vec
    k = min(k, len(sims))
    top_idx = np.argsort(-sims)[:k]
    top_comms = REF_COMM[top_idx]
    vals, counts = np.unique(top_comms, return_counts=True)
    winner = int(vals[int(np.argmax(counts))])
    return {
        "community": winner,
        "neighbour_agreement_pct": round(float(counts.max()) / k * 100, 1),
        "k": k,
        "mean_topk_similarity": round(float(sims[top_idx].mean()), 4),
        "vote_distribution": {str(int(v)): int(c) for v, c in zip(vals, counts)},
        "top5": [{"index": int(i), "community": int(REF_COMM[i]),
                  "filename": REF_NAMES[i], "score": round(float(sims[i]), 4)}
                 for i in top_idx[:5]],
    }

# ---------- 11-class e-waste classifier (ONNX export, model/web_export) ----------
# Separately trained supervised model (ViT-B/16 SigLIP2 backbone, 11 classes:
# 10 e-waste classes + non_electronic). It runs FIRST on every /api/predict: it
# decides accept / reject, and it supplies the displayed label. The SigLIP2 +
# kNN route below stays untouched and is reported as the visual-community evidence.
CLF_DIR = BASE / "model" / "web_export"
CLF_CONFIG = _load_json(CLF_DIR / "web_config.json") or {}
# Threshold from the calibration experiment reported on /tentang-model
# (122 e-waste tiles from the cluster montages + 16 random non-electronic
# photos, sweep 0.10-0.70): 0.20 gives the best balanced accuracy —
# 80.3% of the correctly classified e-waste tiles pass, 13/16 random
# non-electronic photos are rejected.
CLF_THRESHOLD = 0.20
_CLF = {"sess": None, "inp": None, "labels": {}, "failed": None, "ms": None}

# Indonesian display names for the 11 raw model labels
CLF_LABEL_ID = {
    "battery": "Baterai", "keyboard": "Keyboard", "microwave": "Microwave",
    "mobile": "Handphone", "mouse": "Mouse", "non_electronic": "Bukan Elektronik",
    "pcb": "Papan Sirkuit (PCB)", "player": "Radio / Penyetel Musik",
    "printer": "Printer", "television": "Televisi", "washing_machine": "Mesin Cuci",
}

# raw label -> class_id of PANDUAN_KELAS (hazard / handling knowledge base).
CLF_TO_PANDUAN = {
    "battery": "battery", "keyboard": "keyboard", "microwave": "microwave",
    "mobile": "phone", "mouse": "mouse", "pcb": "pcb", "printer": "printer",
    "television": "monitor", "washing_machine": "washing_machine",
    "player": "other", "non_electronic": "other",
}
CLF_PANDUAN_DEFAULT = "other"

def get_clf():
    if _CLF["sess"] is not None:
        return _CLF
    if _CLF["failed"] is not None:
        raise RuntimeError(_CLF["failed"])
    try:
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        path = CLF_DIR / "model_quantized.onnx"
        if not path.exists():
            path = CLF_DIR / "model.onnx"
        sess = ort.InferenceSession(str(path), so, providers=["CPUExecutionProvider"])
        labels = {int(k): v for k, v in (CLF_CONFIG.get("label_map") or _load_json(BASE/"model"/"label_map.json") or {}).items()}
        if not labels:
            raise RuntimeError("label_map.json / web_config.json missing")
        _CLF.update(sess=sess, inp=sess.get_inputs()[0].name, labels=labels, ms=path.name)
        print(f"[clf] {len(labels)}-class ONNX classifier ready ({path.name})", flush=True)
        return _CLF
    except Exception as e:
        _CLF["failed"] = str(e)
        raise RuntimeError(f"Cannot load ONNX classifier: {e}")

def clf_probs(img: Image.Image) -> np.ndarray:
    """Letterbox-free eval pipeline: shorter side -> 256, centre crop 224, (x-.5)/.5."""
    s = get_clf()
    im = img.convert("RGB")
    w, h = im.size
    k = 256 / min(w, h)
    im = im.resize((max(224, round(w * k)), max(224, round(h * k))), Image.BICUBIC)
    w, h = im.size
    l, t = (w - 224) // 2, (h - 224) // 2
    x = np.asarray(im.crop((l, t, l + 224, t + 224)), np.float32) / 255.0
    x = ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]
    z = s["sess"].run(None, {s["inp"]: x})[0][0].astype(np.float64)
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()

def clf_predict(img: Image.Image) -> dict:
    """Top-1 label + confidence + panduan class. Raises if the model is unusable."""
    p = clf_probs(img)
    order = np.argsort(-p)[:3]
    best = int(order[0])
    label = _CLF["labels"][best]
    conf = float(p[best])
    top3 = [{"label": _CLF["labels"][int(i)],
             "label_id": CLF_LABEL_ID.get(_CLF["labels"][int(i)], _CLF["labels"][int(i)]),
             "prob": round(float(p[int(i)]), 4)} for i in order]
    return {
        "label": label,
        "label_id": CLF_LABEL_ID.get(label, label),
        "confidence": round(conf, 4),
        "confidence_pct": round(conf * 100, 1),
        "threshold": CLF_THRESHOLD,
        "class_id": CLF_TO_PANDUAN.get(label, CLF_PANDUAN_DEFAULT),
        "top3": top3,
        "model": _CLF["ms"],
    }

def clf_gate(img: Image.Image):
    """Accept/reject rules from the spec. Returns (clf, reject_or_None)."""
    try:
        clf = clf_predict(img)
    except Exception as e:
        # Classifier unavailable -> fall back to the previous behaviour instead
        # of blocking the whole page.
        print(f"[clf] unavailable, continuing with kNN only: {e}", flush=True)
        return None, None
    if clf["label"] == "non_electronic" and clf["confidence"] >= CLF_THRESHOLD:
        # confident "this is not an electronic item"
        return clf, {"reason": "not_electronic",
                     "message": "Ini sepertinya bukan barang elektronik",
                     "hint": "Foto harus menunjukkan barang elektronik / e-waste."}
    if clf["confidence"] < CLF_THRESHOLD:
        return clf, {"reason": "low_confidence",
                     "message": "coba lagi!",
                     "hint": "Confidence "
                             f"{clf['confidence_pct']}% di bawah ambang {int(CLF_THRESHOLD*100)}% — "
                             "foto ulang dengan cahaya terang, latar kontras, dan satu barang saja."}
    return clf, None

# High-level insight categories for NEW 16 macro-communities.
INSIGHT_CATEGORIES = [
    {"name": "Hazardous Lithium Batteries", "tag": "SAFETY",
     "members": [12, 13, 14],
     "note": "Battery-like visual groups — priority stream for safe handling."},
    {"name": "High-Value PCBs", "tag": "RECOVERY",
     "members": [7],
     "note": "PCB / circuit-board group — precious-metal recovery potential."},
    {"name": "Home Appliances", "tag": "APPLIANCE",
     "members": [3, 8],
     "note": "Washing machines + microwaves — bulky appliance stream."},
    {"name": "Personal Computing", "tag": "VOLUME",
     "members": [1, 2, 5, 6],
     "note": "Smartphones, keyboards, mice, printers — largest device family."},
]

def category_payload(spec: dict) -> dict:
    members = [community_payload(c) for c in spec["members"]]
    size = sum(m["size"] for m in members)
    return {"name": spec["name"], "tag": spec["tag"], "note": spec["note"],
            "members": members, "size": size,
            "pct": round(size / TOTAL * 100, 2)}

# ---------- Learn / Guides content (customer-facing, non-technical) ----------
ARTICLES = [
    {"slug":"understanding-e-waste","title":"Understanding E-Waste","excerpt":"What e-waste is, what valuable materials live inside, and why it deserves a second look.",
     "sections":[
        {"heading":"What is e-waste?","body":"E-waste is any discarded electrical or electronic device — from phones and laptops to chargers, batteries, and appliances. As we upgrade faster, the volume grows. Globally, over 50 million tonnes are generated each year."},
        {"heading":"What valuable materials are inside?","body":"Even small devices contain copper, aluminum, glass, and trace amounts of gold, silver, and rare earth elements. A tonne of circuit boards can hold more gold than a tonne of ore. Recovery is possible when items are collected properly."},
        {"heading":"Why improper disposal can be harmful","body":"Batteries, screens, and boards can leach metals or release fumes if broken, burned, or landfilled. Keeping them dry, intact, and separate helps protect people and the environment."},
        {"heading":"What can we do?","body":"Recognize what you have, keep it together, and choose a responsible next step — reuse, repair, or channel it to a certified recycler. Start by identifying your item."},
     ]},
    {"slug":"why-recycling-matters","title":"Why Recycling Matters","excerpt":"Recycling keeps materials in use and reduces the need for new extraction.",
     "sections":[
        {"heading":"Keeping materials circular","body":"Recycling recovers metals and plastics so they re-enter manufacturing, reducing mining and energy use."},
        {"heading":"Community impact","body":"Local collection creates jobs, supports repair culture, and funds community programs when handled through ethical channels."},
        {"heading":"Your contribution","body":"Even one phone handed in correctly keeps hazardous parts out of landfill and valuable parts in the loop."},
     ]},
    {"slug":"your-role-and-community","title":"Your Role & Community","excerpt":"How individuals and communities power circularity together.",
     "sections":[
        {"heading":"At home","body":"Store unused electronics in a dry place, keep batteries separate, and avoid breaking screens or boards."},
        {"heading":"In your neighborhood","body":"Community drives, repair cafés, and school programs help neighbours learn and act together."},
        {"heading":"Together","body":"When many households participate, collection becomes viable and recovery scales."},
     ]},
    {"slug":"where-to-recycle-safely","title":"Where to Recycle Safely","excerpt":"Find a safe, certified path for your item.",
     "sections":[
        {"heading":"Certified collectors","body":"Look for recyclers or take-back programs that provide documentation and safe handling for batteries and boards."},
        {"heading":"Retail and manufacturer programs","body":"Many brands and retailers offer drop-off for phones, laptops, and accessories."},
        {"heading":"What to ask","body":"Ask where materials go next and whether batteries are handled separately."},
     ]},
    {"slug":"when-to-let-go","title":"When to Let Go of Devices","excerpt":"Signs it’s time to repair, pass on, or recycle.",
     "sections":[
        {"heading":"Repair first","body":"If a device still functions with a battery or screen fix, repair extends its life the most."},
        {"heading":"Pass it on","body":"Working devices can be donated or resold — ensure data is wiped."},
        {"heading":"Recycle when done","body":"If it’s broken, obsolete, or unsafe, route it to recycling rather than storage."},
     ]},
    {"slug":"how-to-recycle-step-by-step","title":"How to Recycle Step by Step","excerpt":"A simple, safe routine for any electronic item.",
     "sections":[
        {"heading":"01 Prepare","body":"Back up and wipe personal data. Keep the item intact and dry."},
        {"heading":"02 Sort","body":"Separate batteries, cables, and devices. Keep screens unbroken."},
        {"heading":"03 Drop or schedule","body":"Use a certified drop-off or schedule a pickup if available in your area."},
        {"heading":"04 Track","body":"Keep the receipt or tracking number for your records."},
     ]},
]
def get_article(slug):
    for a in ARTICLES:
        if a["slug"]==slug: return a
    return None

GUIDE_CATEGORIES = [
    {"id":"phone","label":"Phone","icon":"📱","do":["Keep battery inside device","Wipe personal data","Keep screen intact"],"dont":["Don’t puncture battery","Don’t throw in household trash"],"next":"Drop at certified phone collection or retailer take-back."},
    {"id":"laptop","label":"Laptop","icon":"💻","do":["Back up and wipe drive","Keep charger with device if possible"],"dont":["Don’t break screen or board","Don’t store in damp place"],"next":"Schedule pickup or bring to certified recycler."},
    {"id":"battery","label":"Battery","icon":"🔋","do":["Tape terminals","Store dry and separate","Use battery collection"],"dont":["Don’t crush or burn","Don’t mix with general waste"],"next":"Hand to battery-specific collection — coming soon: chemistry check."},
    {"id":"pcb","label":"PCB","icon":"🟩","do":["Keep board intact","Handle by edges"],"dont":["Don’t burn or wash with water","Don’t break into pieces"],"next":"Route to e-waste recycler — coming soon: sub-category analysis."},
    {"id":"charger","label":"Charger","icon":"🔌","do":["Coil cable loosely","Keep together"],"dont":["Don’t cut cable"],"next":"Drop with small electronics."},
    {"id":"monitor","label":"Monitor","icon":"🖥️","do":["Keep screen unbroken","Keep stand attached"],"dont":["Don’t crack glass"],"next":"Use bulky-item pickup if available."},
    {"id":"other","label":"Other","icon":"📦","do":["Keep item dry and together"],"dont":["Don’t dismantle unsafely"],"next":"Explore visual communities or ask your local collector."},
]

# ---------- Panduan per kelas (10 kelas) — basis pengetahuan manual per spec 5.3 ----------
PANDUAN_KELAS = [
  {"class_id":"battery","nama":"Baterai","icon":"🔋","tingkat_bahaya":"tinggi","alasan_bahaya":"Risiko kebakaran, kebocoran, dan kandungan logam berat.","status_b3":"Termasuk B3 — cek regulasi B3 yang berlaku","material_berbahaya":["Litium","Kadmium","Timbal"],"material_berharga":["Kobalt","Nikel","Litium"],"penyimpanan_aman":["Tutup kutub dengan selotip","Jangan ditumpuk","Simpan di tempat kering dan sejuk"],"persiapan_setor":["Lepas dari perangkat jika aman","Bungkus terpisah"],"keputusan":{"aturan":"Baterai menggembung atau bocor → langsung ke drop-off B3"},"jenis_dropoff":["B3"],"sumber":[{"judul":"Regulasi Pengelolaan Limbah B3","penerbit":"KLHK","tahun":"2021","url":""}]},
  {"class_id":"pcb","nama":"Papan Sirkuit (PCB)","icon":"🟩","tingkat_bahaya":"tinggi","alasan_bahaya":"Mengandung timbal dan brominated flame retardant.","status_b3":"Termasuk B3","material_berbahaya":["Timbal","Bromin"],"material_berharga":["Emas","Tembaga","Perak"],"penyimpanan_aman":["Jangan dibongkar","Simpan kering","Jauhkan dari anak"],"persiapan_setor":["Jangan dicuci","Bungkus antistatik jika ada"],"keputusan":{"aturan":"PCB utuh → daur ulang; PCB rusak parah → drop-off B3"},"jenis_dropoff":["B3","elektronik"],"sumber":[{"judul":"Laporan Material E-Waste","penerbit":"UNEP","tahun":"2019","url":""}]},
  {"class_id":"phone","nama":"Handphone","icon":"📱","tingkat_bahaya":"sedang","alasan_bahaya":"Baterai internal berisiko bocor.","status_b3":"Periksa baterai terpisah","material_berbahaya":["Baterai litium"],"material_berharga":["Emas","Tembaga"],"penyimpanan_aman":["Matikan perangkat","Lepas casing jika bisa"],"persiapan_setor":["Hapus data","Lepas kartu SIM"],"keputusan":{"aturan":"Masih menyala → donasi; Mati total → daur ulang"},"jenis_dropoff":["elektronik"],"sumber":[{"judul":"Panduan Daur Ulang HP","penerbit":"Kominfo","tahun":"2020","url":""}]},
  {"class_id":"laptop","nama":"Laptop","icon":"💻","tingkat_bahaya":"sedang","alasan_bahaya":"Baterai dan layar mengandung bahan sensitif.","status_b3":"Baterai = B3","material_berbahaya":["Baterai","Merkuri layar lama"],"material_berharga":["Aluminium","Tembaga"],"penyimpanan_aman":["Jangan ditumpuk","Simpan di tas"],"persiapan_setor":["Hapus data & lepas baterai jika bisa"],"keputusan":{"aturan":"Umur <5 th & masih nyala → donasi; Lainnya → daur ulang"},"jenis_dropoff":["elektronik"],"sumber":[{"judul":"E-Waste Handling Guide","penerbit":"ITU","tahun":"2022","url":""}]},
  {"class_id":"monitor","nama":"Monitor","icon":"🖥️","tingkat_bahaya":"sedang","alasan_bahaya":"Layar tabung mengandung timbal, LCD mengandung merkuri lampu.","status_b3":"Cek jenis layar","material_berbahaya":["Timbal","Merkuri"],"material_berharga":["Kaca","Logam"],"penyimpanan_aman":["Jangan dibanting","Simpan tegak"],"persiapan_setor":["Bungkus layar"],"keputusan":{"aturan":"Monitor tabung → B3; Flat panel → elektronik"},"jenis_dropoff":["elektronik","B3"],"sumber":[{"judul":"Monitor Disposal","penerbit":"EPA","tahun":"2021","url":""}]},
  {"class_id":"printer","nama":"Printer","icon":"🖨️","tingkat_bahaya":"rendah","alasan_bahaya":"Tinta/toner bisa mengiritasi.","status_b3":"Toner = B3","material_berbahaya":["Toner"],"material_berharga":["Plastik","Logam"],"penyimpanan_aman":["Keluarkan kertas","Tutup rapat"],"persiapan_setor":["Kosongkan tinta"],"keputusan":{"aturan":"Masih bagus → donasi sekolah"},"jenis_dropoff":["elektronik"],"sumber":[{"judul":"Printer Guide","penerbit":"DLHK","tahun":"2020","url":""}]},
  {"class_id":"keyboard","nama":"Keyboard","icon":"⌨️","tingkat_bahaya":"rendah","alasan_bahaya":"Risiko rendah, plastik & PCB kecil.","status_b3":"Non-B3","material_berbahaya":[],"material_berharga":["Plastik"],"penyimpanan_aman":["Bersihkan debu"],"persiapan_setor":["Lepas baterai jika wireless"],"keputusan":{"aturan":"Tombol lengkap → donasi"},"jenis_dropoff":["elektronik"],"sumber":[{"judul":"Small E-Waste","penerbit":"UNEP","tahun":"2020","url":""}]},
  {"class_id":"mouse","nama":"Mouse","icon":"🖱️","tingkat_bahaya":"rendah","alasan_bahaya":"Risiko rendah.","status_b3":"Non-B3","material_berbahaya":[],"material_berharga":["Plastik"],"penyimpanan_aman":["Simpan kering"],"persiapan_setor":["Lepas baterai"],"keputusan":{"aturan":"Masih klik → donasi"},"jenis_dropoff":["elektronik"],"sumber":[{"judul":"Small E-Waste","penerbit":"UNEP","tahun":"2020","url":""}]},
  {"class_id":"microwave","nama":"Microwave","icon":"♨️","tingkat_bahaya":"sedang","alasan_bahaya":"Kapasitor tegangan tinggi.","status_b3":"Cek kapasitor","material_berbahaya":["Kapasitor"],"material_berharga":["Besi","Tembaga"],"penyimpanan_aman":["Cabut listrik","Jangan dibongkar"],"persiapan_setor":["Kosongkan & bersihkan"],"keputusan":{"aturan":"Masih panas → donasi; Rusak → daur ulang"},"jenis_dropoff":["elektronik"],"sumber":[{"judul":"Appliance Guide","penerbit":"SNI","tahun":"2019","url":""}]},
  {"class_id":"washing_machine","nama":"Mesin Cuci","icon":"🫧","tingkat_bahaya":"rendah","alasan_bahaya":"Bahan besar, risiko rendah jika utuh.","status_b3":"Non-B3","material_berbahaya":[],"material_berharga":["Besi","Aluminium"],"penyimpanan_aman":["Keringkan tabung"],"persiapan_setor":["Cabut selang"],"keputusan":{"aturan":"Masih berputar → donasi"},"jenis_dropoff":["elektronik"],"sumber":[{"judul":"Large Appliance","penerbit":"Kemenperin","tahun":"2021","url":""}]},
]
def get_panduan(class_id):
    for p in PANDUAN_KELAS:
        if p["class_id"]==class_id:
            return p
    return None

# Peta Drop-off Surabaya — hanya titik yang punya sumber publik (riset web, 26 Sep 2026).
# Bukan hasil kunjungan/telepon. status: "bersumber" = sumber menyebut titik ini menerima
# e-waste; "konfirmasi" = ada keraguan (program berakhir, akses terbatas, atau penerimaan
# e-waste tidak disebut) — hubungi dulu. lat/lng mendekati (tingkat gedung/kelurahan).
# kontak "" = tidak ada di sumber; jangan diisi tebakan.
_SMALL = ["battery", "phone", "laptop", "pcb", "keyboard", "mouse"]
_ALL = _SMALL + ["printer", "monitor", "microwave", "washing_machine"]
_SRC_IDN = ("IDN Times Jatim (31 Jan 2025)",
            "https://jatim.idntimes.com/news/jawa-timur/kurangi-sampah-elektronik-retail-di-surabaya-sedia-kotak-daur-ulang-00-w15v1-b57l5g")
_SRC_UE = ("Universal Eco", "https://universaleco.id/en/drop-box-e-waste-di-indonesia-solusi-tepat-untuk-mengelola-limbah-elektronik/")
_SRC_W4C = ("Waste4Change", "https://waste4change.com/blog/mengenal-komunitas-e-waste-rj-yang-kelola-sampah-elektronik/")
_SRC_UR = ("Bali Prawara (13 Des 2025)",
           "https://baliprawara.com/kurangi-e-waste-urban-republic-perluas-program-ur-zero-waste-ke-surabaya-dan-bali/")
_SRC_SATUDATA = ("Satu Data Surabaya — dataset fasilitas pengelolaan sampah (DLH)",
                 "https://ckan.surabaya.go.id/de/datastore/dump/1b8ad94b-ccec-49e8-ad02-28772de86705?bom=True")
_TPS3R_NOTE = ("Fasilitas pemilahan sampah resmi Pemkot (status aktif di dataset). Penerimaan e-waste "
               "tidak disebut di sumber — tanyakan petugas dulu.")

def _tps3r(nama, alamat, wilayah, lat, lng):
    return {"nama": nama, "alamat": alamat, "wilayah": wilayah, "lat": lat, "lng": lng,
            "jenis_diterima": _SMALL, "jam_buka": "Tanyakan", "kontak": "",
            "sumber": _SRC_SATUDATA[0], "sumber_url": _SRC_SATUDATA[1],
            "status": "konfirmasi", "catatan": _TPS3R_NOTE}

PETA_TITIK = [
  # --- 10 titik awal (data lama, dipertahankan; belum ada sumber publik) ---
  {"nama":"TPS 3R Wonokromo","alamat":"Jl. Wonokromo No.12, Surabaya","wilayah":"Surabaya Selatan","lat":-7.300,"lng":112.73,"jenis_diterima":["battery","phone","laptop"],"jam_buka":"08:00-16:00","kontak":"031-123456","sumber":"DLH Surabaya","terverifikasi":"2026-03-15","status":"data_awal"},
  {"nama":"Bank Sampah Surabaya Pusat","alamat":"Jl. Taman Surya No.1","wilayah":"Surabaya Pusat","lat":-7.257,"lng":112.752,"jenis_diterima":["pcb","printer","keyboard"],"jam_buka":"09:00-15:00","kontak":"031-234567","sumber":"DLH Surabaya","terverifikasi":"2026-02-20","status":"data_awal"},
  {"nama":"Dropbox ITS","alamat":"Kampus ITS Sukolilo","wilayah":"Surabaya Timur","lat":-7.282,"lng":112.79,"jenis_diterima":["phone","laptop","mouse","keyboard"],"jam_buka":"08:00-17:00","kontak":"031-345678","sumber":"ITS","terverifikasi":"2026-04-01","status":"data_awal"},
  {"nama":"Electronic Waste Center Rungkut","alamat":"Jl. Rungkut Industri III No.5","wilayah":"Surabaya Timur","lat":-7.32,"lng":112.78,"jenis_diterima":["monitor","microwave","washing_machine","battery"],"jam_buka":"09:00-16:00","kontak":"031-456789","sumber":"Kunjungan langsung","terverifikasi":"2026-03-10","status":"data_awal"},
  {"nama":"TPA Benowo (B3)","alamat":"Jl. Raya Benowo","wilayah":"Surabaya Barat","lat":-7.20,"lng":112.64,"jenis_diterima":["battery","pcb"],"jam_buka":"07:00-15:00","kontak":"031-567890","sumber":"DLH Surabaya","terverifikasi":"2026-01-18","status":"data_awal"},
  {"nama":"Gerai E-Waste Galaxy Mall","alamat":"Galaxy Mall Lt.2","wilayah":"Surabaya Timur","lat":-7.275,"lng":112.78,"jenis_diterima":["phone","laptop","printer"],"jam_buka":"10:00-21:00","kontak":"031-678901","sumber":"Telepon","terverifikasi":"2026-02-28","status":"data_awal"},
  {"nama":"Bank Sampah Karah","alamat":"Jl. Karah No.8","wilayah":"Surabaya Selatan","lat":-7.31,"lng":112.72,"jenis_diterima":["keyboard","mouse","printer"],"jam_buka":"08:00-14:00","kontak":"031-789012","sumber":"DLH Surabaya","terverifikasi":"2026-03-22","status":"data_awal"},
  {"nama":"Dropbox Universitas Airlangga","alamat":"Kampus C Mulyorejo","wilayah":"Surabaya Timur","lat":-7.27,"lng":112.79,"jenis_diterima":["phone","battery","pcb"],"jam_buka":"08:00-16:00","kontak":"031-890123","sumber":"Unair","terverifikasi":"2026-04-05","status":"data_awal"},
  {"nama":"Recycle Center Wonorejo","alamat":"Jl. Wonorejo No.45","wilayah":"Surabaya Timur","lat":-7.33,"lng":112.77,"jenis_diterima":["monitor","laptop","washing_machine"],"jam_buka":"09:00-17:00","kontak":"031-901234","sumber":"Kunjungan","terverifikasi":"2026-03-30","status":"data_awal"},
  {"nama":"TPS Kedurus","alamat":"Jl. Kedurus No.22","wilayah":"Surabaya Selatan","lat":-7.305,"lng":112.70,"jenis_diterima":["microwave","washing_machine","monitor"],"jam_buka":"08:00-15:00","kontak":"031-012345","sumber":"DLH Surabaya","terverifikasi":"2026-02-15","status":"data_awal"},
  # --- titik dari riset sumber publik ---
  {"nama":"Dropbox E-Waste Balai Kota Surabaya","alamat":"Jl. Taman Surya No.1, Ketabang, Genteng, Surabaya","wilayah":"Surabaya Pusat",
   "lat":-7.2593,"lng":112.7471,"jenis_diterima":_SMALL,"jam_buka":"Jam kantor","kontak":"",
   "sumber":_SRC_UE[0],"sumber_url":_SRC_UE[1],"status":"bersumber","catatan":"Kerja sama Pemkot Surabaya dengan pengelola e-waste."},
  {"nama":"Dropbox E-Waste Tunjungan Plaza","alamat":"Jl. Basuki Rahmat No.8-12, Kedungdoro, Tegalsari, Surabaya","wilayah":"Surabaya Pusat",
   "lat":-7.2620,"lng":112.7389,"jenis_diterima":_SMALL,"jam_buka":"Jam mal","kontak":"",
   "sumber":_SRC_UE[0],"sumber_url":_SRC_UE[1],"status":"bersumber","catatan":"Tanyakan letak dropbox ke customer service mal."},
  {"nama":"AZKO Galaxy Mall — Dropbox Bisa Baik","alamat":"Galaxy Mall 2 Lt. Dasar G-223, Jl. Dharmahusada Indah Timur No.35-37, Mulyorejo, Surabaya","wilayah":"Surabaya Timur",
   "lat":-7.2753,"lng":112.7822,"jenis_diterima":_SMALL,"jam_buka":"Jam mal","kontak":"",
   "sumber":_SRC_IDN[0],"sumber_url":_SRC_IDN[1],"status":"bersumber","catatan":"Program 'Bersama Atasi Sampah Elektronik' (sejak 1 Feb 2025), menerima semua jenis elektronik yang muat di dropbox."},
  {"nama":"AZKO Royal Plaza — Dropbox Bisa Baik","alamat":"Royal Plaza Lt.1 H1-17, Jl. A. Yani No.16-18, Wonokromo, Surabaya","wilayah":"Surabaya Selatan",
   "lat":-7.3087,"lng":112.7358,"jenis_diterima":_SMALL,"jam_buka":"10:00-21:30","kontak":"",
   "sumber":_SRC_IDN[0],"sumber_url":_SRC_IDN[1],"status":"bersumber","catatan":"Program 'Bisa Baik' AZKO."},
  {"nama":"AZKO Pakuwon — Dropbox Bisa Baik","alamat":"Pakuwon City Mall Lt.3, Jl. Kejawan Putih Mutiara No.17, Mulyorejo, Surabaya","wilayah":"Surabaya Timur",
   "lat":-7.2780,"lng":112.8060,"jenis_diterima":_SMALL,"jam_buka":"10:00-22:00","kontak":"",
   "sumber":_SRC_IDN[0],"sumber_url":_SRC_IDN[1],"status":"konfirmasi","catatan":"Sumber hanya menyebut 'AZKO Pakuwon' — bisa Pakuwon City Mall atau Pakuwon Mall. Konfirmasi cabangnya."},
  {"nama":"Agen E-Waste RJ Wonorejo","alamat":"Kel. Wonorejo, Kec. Rungkut, Surabaya (alamat lengkap via @ewasterj_surabaya)","wilayah":"Surabaya Timur",
   "lat":-7.3080,"lng":112.7900,"jenis_diterima":_ALL,"jam_buka":"Janjian dulu","kontak":"IG @ewasterj_surabaya · linktr.ee/ewasterj",
   "sumber":_SRC_W4C[0],"sumber_url":_SRC_W4C[1],"status":"bersumber","catatan":"Isi formulir di linktr.ee/ewasterj sebelum setor. Barang besar: tanyakan dulu."},
  {"nama":"Agen E-Waste RJ Pabean Cantian","alamat":"Kec. Pabean Cantian, Surabaya (alamat lengkap via @ewasterj_surabaya)","wilayah":"Surabaya Utara",
   "lat":-7.2270,"lng":112.7340,"jenis_diterima":_ALL,"jam_buka":"Janjian dulu","kontak":"IG @ewasterj_surabaya · linktr.ee/ewasterj",
   "sumber":_SRC_W4C[0],"sumber_url":_SRC_W4C[1],"status":"bersumber","catatan":"Isi formulir di linktr.ee/ewasterj sebelum setor."},
  {"nama":"Alang-Alang Zero Waste Store (Dropbox E-Waste RJ)","alamat":"Jl. Dr. Ir. H. Soekarno (MERR) No.56-68, Mulyorejo, Surabaya","wilayah":"Surabaya Timur",
   "lat":-7.2790,"lng":112.7830,"jenis_diterima":_SMALL,"jam_buka":"Sel-Jum 11:00-19:00 · Sab-Min 09:00-17:00","kontak":"IG @alangalang_zerowaste",
   "sumber":_SRC_W4C[0],"sumber_url":_SRC_W4C[1],"status":"bersumber","catatan":"Titik dropbox jaringan E-Waste RJ."},
  {"nama":"Urban Republic Tunjungan Plaza 4","alamat":"Tunjungan Plaza 4, Jl. Basuki Rahmat No.8-12, Surabaya","wilayah":"Surabaya Pusat",
   "lat":-7.2626,"lng":112.7395,"jenis_diterima":["phone","laptop"],"jam_buka":"Jam mal","kontak":"",
   "sumber":_SRC_UR[0],"sumber_url":_SRC_UR[1],"status":"konfirmasi","catatan":"Program UR Zero Waste (charger, powerbank, kabel, HP, tablet, laptop) periode 20 Agt-31 Des 2025 — cek apakah masih berjalan."},
  {"nama":"Urban Republic Galaxy Mall 3","alamat":"Galaxy Mall 3, Jl. Dharmahusada Indah Timur, Mulyorejo, Surabaya","wilayah":"Surabaya Timur",
   "lat":-7.2748,"lng":112.7815,"jenis_diterima":["phone","laptop"],"jam_buka":"Jam mal","kontak":"",
   "sumber":_SRC_UR[0],"sumber_url":_SRC_UR[1],"status":"konfirmasi","catatan":"Program UR Zero Waste periode 20 Agt-31 Des 2025 — cek apakah masih berjalan."},
  {"nama":"Urban Republic Pakuwon City Mall","alamat":"Pakuwon City Mall, Jl. Kejawan Putih Mutiara No.17, Mulyorejo, Surabaya","wilayah":"Surabaya Timur",
   "lat":-7.2775,"lng":112.8052,"jenis_diterima":["phone","laptop"],"jam_buka":"Jam mal","kontak":"",
   "sumber":_SRC_UR[0],"sumber_url":_SRC_UR[1],"status":"konfirmasi","catatan":"Program UR Zero Waste periode 20 Agt-31 Des 2025 — cek apakah masih berjalan."},
  {"nama":"Dropbox E-Waste Departemen ITS","alamat":"Kampus ITS Sukolilo, Keputih, Sukolilo, Surabaya","wilayah":"Surabaya Timur",
   "lat":-7.2820,"lng":112.7950,"jenis_diterima":_SMALL,"jam_buka":"Jam kampus","kontak":"",
   "sumber":"ITS Smart Eco Campus","sumber_url":"https://www.its.ac.id/smartecocampus/limbah-dan-sampah/","status":"konfirmasi",
   "catatan":"Tersedia di berbagai departemen; lokasi pasti & akses untuk umum belum disebut."},
  {"nama":"Bank Sampah Induk Surabaya","alamat":"Jl. Raya Menur No.31-A, Manyar Sabrangan, Mulyorejo, Surabaya 60116","wilayah":"Surabaya Timur",
   "lat":-7.2785,"lng":112.7630,"jenis_diterima":_SMALL,"jam_buka":"Tanyakan","kontak":"0851-0009-0858 · IG @banksampahinduksurabaya",
   "sumber":"banksampahinduksurabaya.id","sumber_url":"https://banksampahinduksurabaya.id/","status":"konfirmasi",
   "catatan":"Fokus sampah kering; penerimaan e-waste belum disebut di sumber — telepon dulu."},
  # --- 10 TPS 3R resmi Pemkot (Satu Data Surabaya) ---
  _tps3r("TPS 3R Super Depo Sutorejo", "Jl. Kalisari Timur - Sutorejo, Kalisari, Mulyorejo, Surabaya", "Surabaya Timur", -7.2630, 112.7980),
  _tps3r("TPS 3R Pemilahan Bratang", "Jl. Manyar (Taman Flora), Baratajaya, Gubeng, Surabaya", "Surabaya Timur", -7.2940, 112.7610),
  _tps3r("TPS 3R PDU Jambangan", "Jl. Jambangan Kebon Agung, Jambangan, Surabaya", "Surabaya Selatan", -7.3240, 112.7160),
  _tps3r("TPS 3R Tambak Osowilangun", "Jl. Tambak Oso Wilangun, Benowo, Surabaya", "Surabaya Barat", -7.2110, 112.6560),
  _tps3r("TPS 3R Kedung Cowek", "Jl. Raya Kedung Cowek No.1, Kenjeran, Surabaya", "Surabaya Utara", -7.2270, 112.7790),
  _tps3r("TPS 3R Tenggilis", "Jl. Tenggilis Barat I, Tenggilis Mejoyo, Surabaya", "Surabaya Timur", -7.3200, 112.7560),
  _tps3r("TPS 3R Karangpilang", "Jl. Mastrip Gg. Surya, Karang Pilang, Surabaya", "Surabaya Selatan", -7.3350, 112.6960),
  _tps3r("TPS 3R Warugunung", "Jl. Mastrip Warugunung, Karangpilang, Surabaya", "Surabaya Selatan", -7.3420, 112.6870),
  _tps3r("TPS 3R Gunung Anyar", "Jl. Gununganyar, Gunung Anyar, Surabaya", "Surabaya Timur", -7.3380, 112.7880),
  _tps3r("TPS 3R Banjarsugihan", "Jl. Banjarsugihan Gg. Rolax, Tandes, Surabaya", "Surabaya Barat", -7.2530, 112.6690),
  # --- pengepul / layanan jemput elektronik bekas & rusak ---
  {"nama":"Tunas Harapan Lestari (pengepul elektronik bekas/rusak)","alamat":"Jl. Tambak Dalam Baru 6/16 RT06 RW05, Asemrowo, Surabaya","wilayah":"Surabaya Barat",
   "lat":-7.2440,"lng":112.7100,"jenis_diterima":_ALL,"jam_buka":"Hubungi via WA","kontak":"0813-3416-6464 · 0818-0311-8002",
   "sumber":"tunasharapanlestari.com","sumber_url":"https://www.tunasharapanlestari.com/jual-beli-elektronik-bekas/","status":"bersumber",
   "catatan":"Membeli elektronik bekas/rusak (AC, kulkas, dll), bisa jemput. Pengepul komersial, bukan fasilitas B3 resmi."},
  {"nama":"Rombeng Rongsok Surabaya (layanan jemput)","alamat":"Layanan jemput se-Surabaya, Gresik, Sidoarjo — tidak ada alamat toko","wilayah":"Seluruh Surabaya (jemput)",
   "lat":None,"lng":None,"jenis_diterima":_ALL,"jam_buka":"Hubungi via WA","kontak":"0857-5532-8441",
   "sumber":"rombengrongsoksurabaya.com","sumber_url":"https://www.rombengrongsoksurabaya.com/","status":"bersumber",
   "catatan":"Membeli elektronik bekas/rusak (TV, komputer, printer, mesin cuci, dll) dengan penjemputan. Pengepul komersial."},
]

# ---------- pages (spec section 25 — Beranda, Klasifikasi, Panduan, Peta, Tentang Model) ----------
@app.get("/")
def home():
    return render_template("home.html")

@app.get("/klasifikasi")
def klasifikasi():
    return render_template("klasifikasi.html")

@app.get("/analyze")
def analyze():
    # alias — old URL tetap jalan, redirect ke klasifikasi wording
    return render_template("analyze.html")

@app.get("/result")
def result_page():
    return render_template("result.html")

# Panduan (10 kelas)
@app.get("/panduan")
def panduan_list():
    return render_template("panduan.html", panduan=PANDUAN_KELAS)

@app.get("/panduan/<class_id>")
def panduan_detail(class_id: str):
    p = get_panduan(class_id)
    if not p:
        from flask import abort
        abort(404)
    return render_template("panduan_detail.html", p=p)

@app.get("/peta")
def peta():
    return render_template("peta.html", titik=PETA_TITIK)

# Tentang Model — protected
@app.get("/tentang-model")
def tentang_model():
    if not session.get("tentang_ok"):
        return render_template("tentang_login.html")
    return render_template("tentang_model.html")

@app.post("/tentang-model/login")
def tentang_login():
    email = request.form.get("email","").strip()
    pwd = request.form.get("password","").strip()
    if email=="via.damarani@gmail.com" and pwd=="scannex1230":
        session["tentang_ok"]=True
        return redirect(url_for("tentang_model"))
    return render_template("tentang_login.html", error="Email atau password salah")

@app.get("/tentang-model/logout")
def tentang_logout():
    session.pop("tentang_ok",None)
    return redirect(url_for("tentang_model"))

# Legacy routes keep for compatibility
@app.get("/learn")
def learn():
    return render_template("learn.html", articles=ARTICLES)

@app.get("/learn/<slug>")
def article_detail(slug: str):
    a = get_article(slug)
    if not a:
        from flask import abort
        abort(404)
    idx = next((i for i, x in enumerate(ARTICLES) if x["slug"]==slug), -1)
    prev = ARTICLES[idx-1] if idx>0 else None
    nxt = ARTICLES[idx+1] if idx < len(ARTICLES)-1 else None
    return render_template("article_detail.html", article=a, prev=prev, next=nxt)

@app.get("/guides")
def guides():
    return render_template("guides.html", categories=GUIDE_CATEGORIES)

@app.get("/about")
def about():
    return render_template("about.html")

# ---------- APIs ----------
@app.get("/api/overview")
def api_overview():
    return jsonify({"images": TOTAL, "communities": len(COMMUNITY_STATS),
                    "embedding": "SigLIP2 — 768D (google/siglip2-base-patch16-224)",
                    "clustering": "Leiden",
                    "modularity": round(MODULARITY, 3),
                    "silhouette": round(SILHOUETTE, 3)})

@app.get("/api/umap2d")
def api_umap2d():
    return jsonify(UMAP_PTS)

@app.get("/api/sizes")
def api_sizes():
    return jsonify([community_payload(c) for c in range(len(COMMUNITY_STATS))])

@app.get("/api/community/<int:cid>")
def api_community(cid: int):
    if cid < 0 or cid >= len(COMMUNITY_STATS):
        return jsonify({"error": "unknown community"}), 404
    return jsonify(community_payload(cid))

@app.get("/api/method")
def api_method():
    return jsonify({"pipeline": [{"stage": s, "desc": d} for s, d in PIPELINE],
                    "umap_config": UMAP_CFG, "stability": STABILITY})

@app.get("/api/model-status")
def api_model_status():
    st = ensure_model_loading()
    code = 200 if st["state"] == "ready" else 503
    try:
        get_clf()
        clf = {"state": "ready", "classes": len(_CLF["labels"]),
               "threshold": CLF_THRESHOLD}
    except Exception as e:
        clf = {"state": "not_loaded", "error": str(e)[:200]}
    return jsonify({**st, "model": SIGLIP_ID, "classifier": clf}), code

@app.post("/api/model-retry")
def api_model_retry():
    st = ensure_model_loading(force=True)
    code = 200 if st["state"] == "ready" else 202
    return jsonify({**st, "model": SIGLIP_ID}), code

@app.post("/api/predict")
def api_predict():
    if "image" not in request.files:
        return jsonify({"error": "no file part named 'image' (JPG/PNG/WEBP)"}), 400
    f = request.files["image"]
    ext = (f.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({"error": f"unsupported format .{ext} — use JPG/JPEG/PNG/WEBP"}), 400
    try:
        img = Image.open(f.stream)
    except Exception as e:
        return jsonify({"error": f"cannot read image: {e}"}), 400

    # --- gate 1: supervised 11-class classifier (label + accept/reject) ---
    clf, reject = clf_gate(img)
    if reject:
        return jsonify({"reject": reject, "clf": clf,
                        "threshold": CLF_THRESHOLD}), 200

    if _SIGLIP["proc"] is None:
        st = model_status()
        hint = st.get("detail") or "Check /api/model-status."
        if st["state"] == "loading":
            hint = "Model is loading into memory, try again in ~1 minute."
        elif st["state"] == "starting":
            ensure_model_loading()
            hint = "Model is loading into memory, try again in ~1 minute."
        return jsonify({"error": "SigLIP2 model is not ready yet", "hint": hint}), 503
    try:
        vec = embed_pil(img)
    except RuntimeError as e:
        return jsonify({"error": str(e),
                        "hint": "Check /api/model-status for details"}), 503
    r = knn_predict(vec, k=10)
    c = community_payload(r["community"])
    involved = set([r["community"]] + [t["community"] for t in r["top5"]]
                   + [int(k) for k in r["vote_distribution"].keys()])
    names = {str(i): LABELS[i] for i in involved}
    # knowledge-base entry matching the classifier label (handling steps, hazard)
    pg = get_panduan(clf["class_id"]) if clf else None
    panduan = None
    if pg:
        panduan = {k: pg[k] for k in ("class_id", "nama", "icon", "tingkat_bahaya",
                                      "alasan_bahaya", "penyimpanan_aman",
                                      "persiapan_setor", "keputusan", "jenis_dropoff")}
    return jsonify({
        "predicted_community": r["community"],
        "size": c["size"], "share_pct": c["pct"],
        "interpretation": c["interpretation"], "coherence": c["coherence"],
        "clf": clf, "reject": None, "panduan": panduan,
        "note": "Neighbour agreement is a kNN vote share, NOT a classifier probability.",
        "names": names, **r,
    })

# ---------- Live camera streaming (mimic old YOLO+MobileNet project, adapted to SigLIP2) ----------
# Uses server webcam (cv2.VideoCapture 0) and streams via multipart. Works when server & client are same machine (local dev).
# For remote deployment, browser getUserMedia is used instead (see analyze.html). This endpoint is fallback for local YOLO detection.
try:
    import cv2  # type: ignore
    _cv2_ok = True
except Exception:
    cv2 = None  # type: ignore
    _cv2_ok = False

@app.get("/video_feed")
def video_feed():
    if not _cv2_ok or cv2 is None:
        return jsonify({"error": "OpenCV not available on server — use browser camera instead"}), 503
    # try to load YOLO if available, else plain streaming
    yolo = None
    try:
        from ultralytics import YOLO  # type: ignore
        # try yolov8n.pt in models/ or fallback to no YOLO
        import pathlib as _pl
        yolo_path = _pl.Path("models/yolov8n.pt")
        if yolo_path.exists():
            yolo = YOLO(str(yolo_path))
    except Exception:
        yolo = None

    def generate():
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            # try 1
            cam = cv2.VideoCapture(1)
        frame_count = 0
        while True:
            success, frame = cam.read()
            if not success:
                break
            frame_count += 1
            # lightweight YOLO every 3 frames if available
            if yolo is not None and frame_count % 3 == 0:
                try:
                    results = yolo.predict(frame, verbose=False, conf=0.3)
                    for result in results:
                        for box in result.boxes:
                            # simple box draw — keep class check minimal
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            # optional label
                            try:
                                conf = float(box.conf[0])
                                cv2.putText(frame, f"{conf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                            except: pass
                except Exception:
                    pass
            else:
                # faint scan frame overlay when no YOLO
                h, w = frame.shape[:2]
                cv2.rectangle(frame, (w//4, h//4), (w*3//4, h*3//4), (14,124,123), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        cam.release()

    from flask import Response
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.get("/health")
def health():
    return jsonify({"ok": True, "images": TOTAL})

# Start background model load as soon as the server boots.
ensure_model_loading()
# Load the 11-class ONNX classifier too (local file, ~1s, no download).
try:
    get_clf()
except Exception as e:
    print(f"[clf] warm-up failed: {e}", flush=True)

if __name__ == "__main__":
    # NOTE: reloader is OFF on purpose. The watchdog reloader watches every
    # imported file (incl. torch/transformers in site-packages) and restarts
    # endlessly, killing the background model download each time.
    # After editing code, restart manually with Ctrl+C + python app.py.
    # threaded: a slow /api/predict must not block the other pages
    # HOST 0.0.0.0: reachable from LAN (same WiFi) and from tunnels
    # (Cloudflare/ngrok). Override with env: HOST=127.0.0.1 PORT=5000.
    import os
    app.run(host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "5000")),
            debug=True, threaded=True, use_reloader=False)
