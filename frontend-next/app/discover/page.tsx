"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false }) as any;
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000";

export default function DiscoverPage() {
  const [umap, setUmap] = useState<any[]>([]);
  const [sizes, setSizes] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    fetch(`${API_URL}/api/umap2d`).then(r=>r.json()).then(setUmap).catch(()=>{});
    fetch(`${API_URL}/api/sizes`).then(r=>r.json()).then(setSizes).catch(()=>{});
  }, []);

  const label: Record<number,string> = {};
  sizes.forEach((s:any)=> label[s.id]=s.interpretation);

  const filtered = umap.filter((p:any)=>{
    const name = (label[p.c]||"").toLowerCase();
    const matchQ = !q || name.includes(q.toLowerCase()) || String(p.c).includes(q) || p.f.toLowerCase().includes(q.toLowerCase());
    const matchF = filter==="all" || String(p.c)===filter;
    return matchQ && matchF;
  });

  const by: Record<string, any[]> = {};
  filtered.forEach((p:any)=>{ const l = label[p.c] || `Visual group ${p.c}`; (by[l]=by[l]||[]).push(p); });
  const traces = Object.keys(by).sort().map(l=>({
    x: by[l].map(p=>p.x), y: by[l].map(p=>p.y), mode:"markers", type:"scattergl", name:l, text: by[l].map(p=> `${l} · ${p.f}`), marker:{size:5, opacity:0.75}
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Discover electronic waste</h1>
      <p className="mt-2 text-slate-600 max-w-2xl">Explore visual patterns discovered across thousands of electronic-waste images. Each point is one image, each color is one visual group.</p>

      <div className="mt-6 flex flex-wrap gap-3 items-center">
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search visual group or filename…" className="border border-slate-200 rounded-full px-4 py-2 text-sm w-64 focus:outline-none focus:border-[#0e7c7b]" />
        <select value={filter} onChange={e=>setFilter(e.target.value)} className="border border-slate-200 rounded-full px-4 py-2 text-sm">
          <option value="all">All visual groups (16)</option>
          {sizes.map((s:any)=><option key={s.id} value={String(s.id)}>{s.interpretation} — {s.size}</option>)}
        </select>
        <span className="text-xs text-slate-500">{filtered.length.toLocaleString()} / {umap.length.toLocaleString()} shown</span>
      </div>

      <div className="mt-6 rounded-3xl border border-slate-200 bg-white p-2 sm:p-4">
        <div className="h-[560px]">
          {umap.length===0 ? <div className="h-full grid place-items-center text-sm text-slate-500">Loading visual map… (needs Flask running)</div> :
            <Plot data={traces} layout={{ paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", margin:{t:10, l:40, r:10, b:40}, legend:{orientation:"h"}, xaxis:{title:""}, yaxis:{title:""} } as any} style={{width:"100%",height:"100%"}} config={{responsive:true, displayModeBar:true}} />
          }
        </div>
        <p className="mt-3 text-xs text-slate-400 text-center">Zoom, pan, hover, search, and filter — interactions stay on the visualization, no raw technical logs.</p>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <a href="/communities" className="text-sm font-semibold text-[#0e7c7b] hover:underline">View all visual communities →</a>
        <span className="text-slate-300">·</span>
        <a href="/analyze" className="text-sm font-semibold text-[#0e7c7b] hover:underline">Analyze an item →</a>
      </div>
    </div>
  );
}
