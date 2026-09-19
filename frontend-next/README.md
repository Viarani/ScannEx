# E-Waste Intelligence — Next.js (Vercel) + Flask (Render)

## Run locally
```bash
# 1) Flask (in ewaste_dashboard/)
python app.py  # http://127.0.0.1:5000  (needs SIGLIP2 1.5GB once)
# 2) Next.js
cd frontend-next
npm install
cp .env.example .env.local  # set NEXT_PUBLIC_API_URL
npm run dev  # http://localhost:3000
```

## Deploy
- Vercel: import `frontend-next/`, set env `NEXT_PUBLIC_API_URL=https://api.yourapp.onrender.com`, deploy.
- Flask: deploy `ewaste_dashboard/` to Render/Railway/Fly (Docker, 4GB RAM). Set `HOST=0.0.0.0`, `PORT=10000` (Render provides).
- `next.config.mjs` rewrites `/api/flask/*` -> Flask for same-origin fallback.

## Data contract (Flask -> Next.js)
`GET /api/overview {images, communities, modularity, silhouette}`
`GET /api/sizes [{id,size,pct,interpretation,coherence}]`  # now 16, aggregated bar by name
`GET /api/umap2d [{i,x,y,c,f}]`
`POST /api/predict multipart image -> {predicted_community, interpretation, neighbour_agreement_pct, size, share_pct, top5, names}`
`GET /api/model-status {state, detail}`

Live camera: `app/scan/page.tsx` uses `getUserMedia` -> `canvas.toBlob` throttled 1/1.5s -> POST predict. Requires HTTPS (Vercel is HTTPS).
