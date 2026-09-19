# E-Waste Intelligence (Flask, SigLIP2)

5-page platform: **Overview → Discovery → Communities → Community detail → Analyze → Insights**
(`+` JSON APIs). Run: `pip install -r requirements.txt`, then `python app.py` → http://127.0.0.1:5000

## Input folder (what each file is)
Canonical source: `results (3)/results` — **SigLIP2 files only** (ignore `dinov2_*`):

| File | What it is | Used for |
|---|---|---|
| `clustering/siglip2_leiden_results.csv` | 3,637 rows: `filepath,label(berat→Electronic),width,height,...,siglip_community` | community id per image, filenames |
| `clustering/siglip2_community_sizes.csv` | 64 rows: `community,size,pct` | cards, bar chart, explorer |
| `embeddings/siglip2_embeddings_l2norm.npy` | (3637,768) float32, L2-normalized | cosine kNN for uploads + centroids |
| `embeddings/siglip2_embeddings.npy` | (3637,768) raw (same size) | not needed (L2 version is used) |
| `embeddings/siglip2_filepaths.csv` | row order ↔ embeddings | order check |
| `embeddings/siglip2_umap_hd.npy` | (3637,15) intermediate UMAP (15D, cosine, n_neighbors=15, seed 42) | 15D config only; 2D recomputed in `prepare_dashboard_data.py` |
| `reports/siglip2_vs_dinov2_comparison.csv` | SigLIP: 768D, 64 clusters, modularity **0.961**, silhouette **0.414** | overview cards |
| `reports/stability_analysis_siglip2.csv` | seed/knn/resolution sweeps | (optional section) |
| `reports/umap_config_siglip2.json` | n_neighbors=15, min_dist=0, 15 comps, cosine, seed 42 | provenance |
| `reports/duplicate_mapping.csv` | exact-duplicate groups | (optional) |
| `reports/siglip2_cluster_interpretation_TEMPLATE.csv` | empty template — no verified labels | why dashboard says "tentative / pending review" |
| `visualizations/community_sizes.png`, `umap_2d_siglip2.png` | static renders | shown under interactive charts |
| `representatives/community_XX/representative_filepaths.txt` | Kaggle-path top reps per community | explorer filename lists |
| `results (4)/output_full_clusters/community_XX.png` | 64 montage images (only viewable images; originals are Kaggle paths) | resized → `static/communities/*.jpg` |

SigLIP checkpoint (from `results (3)/__huggingface_repos__.json`): **`google/siglip2-base-patch16-224`**.

## Run
```
pip install -r requirements.txt
python prepare_dashboard_data.py   # once (UMAP2D + centroids + thumbnails)
python app.py                      # http://127.0.0.1:5000
```
Upload page: `/search`. First upload downloads the SigLIP2 model from HuggingFace (needs internet once).

## Website input/output (MVP)
- **Input:** 1 photo (JPG/JPEG/PNG/WEBP). Nothing else.
- **Pipeline:** SigLIP2 → 768D → L2 norm → cosine kNN (k=10) vs 3,637 refs → majority community + neighbour agreement.
- **Output:** predicted community, tentative interpretation, neighbour agreement %, community stats, montage, top-5 similar refs.
