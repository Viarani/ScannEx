"""Precompute dashboard data from SigLIP2 results (results (3)).

Inputs (canonical, SigLIP2 only):
  data/siglip2_leiden_results.csv
  data/siglip2_community_sizes.csv
  data/siglip2_embeddings_l2norm.npy
  data/siglip2_filepaths.csv
  C:/.../results (3)/results/representatives/community_XX/representative_filepaths.txt
  C:/.../results (4)/output_full_clusters/community_XX.png  (viewable montages only)

Outputs:
  data/umap_2d.json            [{i,x,y,c,f}]
  data/community_stats.json    [{id,size,pct,rep_files,montage}]
  data/similar_communities.json {cid:[{id,score}]}
  data/representatives.json    {cid:[kaggle paths]}
  static/communities/community_XX.jpg  (resized montages)
"""
import csv
import json
import os
import pathlib
import shutil

import numpy as np

BASE = pathlib.Path(__file__).parent
DATA = BASE / "data"
SRC_RESULTS3 = pathlib.Path(
    r"C:\Users\viada\Documents\VSCode\Satria Data 26\Semifinal\64 Cluster\results (3)\results"
)
SRC_MONTAGE = pathlib.Path(
    r"C:\Users\viada\Documents\VSCode\Satria Data 26\Semifinal\64 Cluster\results (4)\output_full_clusters"
)
STATIC_COMM = BASE / "static" / "communities"

# ---------- 1. load leiden results ----------
rows = list(csv.DictReader(open(DATA / "siglip2_leiden_results.csv", encoding="utf-8")))
sizes = {r["community"]: (int(r["size"]), float(r["pct"])) for r in csv.DictReader(open(DATA / "siglip2_community_sizes.csv", encoding="utf-8"))}
index_community = [int(r["siglip_community"]) for r in rows]
basenames = [r["filepath"].split("/")[-1] for r in rows]
print(f"rows={len(rows)} communities={len(sizes)}")

emb = np.load(DATA / "siglip2_embeddings_l2norm.npy").astype(np.float32)
assert emb.shape[0] == len(rows), (emb.shape, len(rows))
print("emb", emb.shape)

# ---------- 2. UMAP 2D for interactive scatter ----------
print("computing UMAP 2D ...")
try:
    import umap
    reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1,
                        metric="cosine", random_state=42)
    xy = reducer.fit_transform(emb)
    print("umap ok", xy.shape)
except Exception as e:
    print("umap failed, PCA fallback:", e)
    from sklearn.decomposition import PCA
    xy = PCA(n_components=2, random_state=42).fit_transform(emb)

xy = np.asarray(xy, dtype=np.float32)
umap_pts = [
    {"i": i, "x": float(xy[i, 0]), "y": float(xy[i, 1]),
     "c": index_community[i], "f": basenames[i]}
    for i in range(len(rows))
]
json.dump(umap_pts, open(DATA / "umap_2d.json", "w"), separators=(",", ":"))
print("wrote umap_2d.json", len(umap_pts))

# ---------- 3. centroids + similar communities ----------
print("computing centroids ...")
cids = sorted(sizes, key=lambda x: int(x))
centroids = {}
for cid in cids:
    idx = [i for i, c in enumerate(index_community) if c == int(cid)]
    m = emb[idx].mean(axis=0)
    m = m / (np.linalg.norm(m) + 1e-12)
    centroids[int(cid)] = m
C = np.stack([centroids[int(c)] for c in cids])  # (64,768)
sim = C @ C.T
similar = {}
for k, cid in enumerate(cids):
    order = np.argsort(-sim[k])
    top = [int(cids[j]) for j in order if int(cids[j]) != int(cid)][:3]
    similar[str(int(cid))] = [
        {"id": t, "score": round(float(sim[k, cids.index(str(t))]), 4)} for t in top
    ]
json.dump(similar, open(DATA / "similar_communities.json", "w", encoding="utf-8"), indent=1)
print("wrote similar_communities.json")

# ---------- 4. representatives (kaggle paths -> basenames) ----------
reps = {}
for cid in range(64):
    txt = SRC_RESULTS3 / "representatives" / f"community_{cid:02d}" / "representative_filepaths.txt"
    if txt.exists():
        paths = [l.strip() for l in open(txt, encoding="utf-8") if l.strip()]
    else:
        paths = []
    reps[str(cid)] = paths
json.dump(reps, open(DATA / "representatives.json", "w", encoding="utf-8"))
print("wrote representatives.json")

stats = []
for cid in range(64):
    size, pct = sizes[str(cid)]
    rep_basenames = [p.split("/")[-1] for p in reps[str(cid)][:8]]
    montage = f"community_{cid:02d}.jpg" if (SRC_MONTAGE / f"community_{cid:02d}.png").exists() else None
    stats.append({"id": cid, "size": size, "pct": round(pct, 2),
                  "rep_files": rep_basenames, "montage": montage})
json.dump(stats, open(DATA / "community_stats.json", "w", encoding="utf-8"), indent=1)
print("wrote community_stats.json")

# ---------- 5. thumbnails of montages ----------
print("resizing montages (64 files, may take a few minutes) ...")
from PIL import Image
STATIC_COMM.mkdir(parents=True, exist_ok=True)
done, skipped = 0, 0
for cid in range(64):
    src = SRC_MONTAGE / f"community_{cid:02d}.png"
    dst = STATIC_COMM / f"community_{cid:02d}.jpg"
    if dst.exists():
        done += 1
        continue
    if not src.exists():
        skipped += 1
        continue
    try:
        im = Image.open(src).convert("RGB")
        if im.width > 1280:
            im = im.resize((1280, int(im.height * 1280 / im.width)), Image.LANCZOS)
        im.save(dst, "JPEG", quality=70, optimize=True)
        done += 1
        if cid % 8 == 0:
            print(f"  ... {done}/64")
    except Exception as e:
        print(f"  WARN {src.name}: {e}")
        skipped += 1
print(f"montages done={done} skipped={skipped}")
total_mb = sum(p.stat().st_size for p in STATIC_COMM.glob("*.jpg")) / 1e6 if list(STATIC_COMM.glob("*.jpg")) else 0
print(f"static/communities size: {total_mb:.1f} MB")
print("DONE")
