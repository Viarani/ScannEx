"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000";

export default function CommunitiesPage() {
  const [data, setData] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"largest"|"smallest">("largest");

  useEffect(()=>{ fetch(`${API_URL}/api/sizes`).then(r=>r.json()).then(setData).catch(()=>{}); }, []);

  let filtered = data.filter((c:any)=> !q || c.interpretation.toLowerCase().includes(q.toLowerCase()) || String(c.id).includes(q));
  filtered = [...filtered].sort((a,b)=> sort==="largest" ? b.size - a.size : a.size - b.size);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Visual Communities</h1>
      <p className="mt-2 text-slate-600">Explore groups of electronic items that share visual characteristics — 16 macro-communities from 3,637 images.</p>

      <div className="mt-6 flex flex-wrap gap-3 items-center">
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search visual group…" className="border border-slate-200 rounded-full px-4 py-2 text-sm w-64" />
        <select value={sort} onChange={e=>setSort(e.target.value as any)} className="border border-slate-200 rounded-full px-4 py-2 text-sm">
          <option value="largest">Largest communities</option>
          <option value="smallest">Smallest communities</option>
        </select>
        <span className="text-xs text-slate-500">{filtered.length} visual groups</span>
      </div>

      <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {filtered.map((c:any)=> (
          <Link key={c.id} href={`/communities/${c.id}`} className="rounded-2xl border border-slate-100 bg-white overflow-hidden hover:shadow-md transition">
            <div className="aspect-[4/3] bg-slate-100 grid place-items-center p-4 text-center">
              <div>
                <div className="text-xs font-bold tracking-widest text-slate-500">VISUAL GROUP {String(c.id).padStart(2,"0")}</div>
                <div className="mt-2 text-sm font-semibold text-slate-900 line-clamp-2">{c.interpretation}</div>
                <div className="mt-1 text-xs text-slate-500">{c.size} images · {c.pct}%</div>
              </div>
            </div>
            <div className="p-4">
              <div className="text-sm font-bold text-slate-900">Community {String(c.id).padStart(2,"0")}</div>
              <div className="text-xs text-slate-500">{c.coherence}</div>
              <div className="mt-2 text-xs font-semibold text-[#0e7c7b]">Explore →</div>
            </div>
            {/* representative thumbnails — using rep_files filenames as placeholder; replace with real thumbs when available */}
            <div className="px-3 pb-3 flex gap-1.5 overflow-hidden">
              {(c.rep_files||[]).slice(0,4).map((f:string)=><div key={f} className="flex-1 aspect-square rounded-lg bg-slate-50 border border-slate-100 grid place-items-center text-[8px] text-slate-400 p-1 text-center leading-tight truncate">{f}</div>)}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
