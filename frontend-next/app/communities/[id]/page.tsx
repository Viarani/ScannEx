"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000";

export default function CommunityDetail({ params }: { params: { id: string } }) {
  const id = params.id;
  const [c, setC] = useState<any>(null);
  const [err, setErr] = useState("");

  useEffect(()=>{ fetch(`${API_URL}/api/community/${id}`).then(async r=>{ if(!r.ok) throw new Error(await r.text()); return r.json(); }).then(setC).catch(e=>setErr(String(e.message||e))); }, [id]);

  if (err) return <div className="max-w-3xl mx-auto px-4 py-16 text-center"><p className="text-red-600 text-sm">{err}</p><Link href="/communities" className="mt-4 inline-block text-[#0e7c7b] font-semibold">Back to communities</Link></div>;
  if (!c) return <div className="max-w-7xl mx-auto px-4 py-10 text-sm text-slate-500">Loading visual group…</div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Link href="/communities" className="text-sm text-slate-500 hover:text-slate-700">← Visual Communities</Link>
      <p className="mt-4 text-xs font-bold tracking-[0.2em] text-[#0e7c7b]">COMMUNITY {String(c.id).padStart(2,"0")}</p>
      <h1 className="mt-2 text-3xl font-extrabold text-slate-900">{c.interpretation}</h1>
      <p className="mt-1 text-sm text-slate-500">Tentative visual interpretation — based on visual inspection, not ground-truth label</p>

      <div className="mt-6 flex flex-wrap gap-4 text-sm">
        <span className="px-3 py-1 rounded-full bg-slate-900 text-white font-semibold">{c.size} visual items</span>
        <span className="px-3 py-1 rounded-full border border-slate-200">{c.pct}% of dataset</span>
        <span className="px-3 py-1 rounded-full border border-slate-200">{c.coherence}</span>
      </div>

      <div className="mt-8 rounded-3xl border border-slate-200 bg-white p-6">
        <h2 className="font-bold text-slate-900">Visual interpretation</h2>
        <p className="mt-1 text-slate-700">{c.interpretation}</p>
        <p className="text-xs text-slate-500 mt-1">Source: {c.source}</p>
      </div>

      <div className="mt-8">
        <h2 className="font-bold text-slate-900">Explore this visual group</h2>
        <p className="text-sm text-slate-500">Representative and member images from this community.</p>
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
          {(c.rep_files||[]).map((f:string)=><div key={f} className="aspect-square rounded-xl bg-slate-100 border border-slate-200 grid place-items-center p-2 text-center text-xs text-slate-500">{f}</div>)}
        </div>
        <p className="mt-2 text-xs text-slate-400">Showing {c.rep_files?.length || 0} representative files. Full gallery can be added when thumbnails are exposed via Flask static.</p>
      </div>

      <div className="mt-10 rounded-2xl bg-slate-50 border border-slate-100 p-6">
        <h3 className="font-bold">Similar visual groups</h3>
        <div className="mt-3 flex flex-wrap gap-3">
          {(c.similar||[]).map((s:any)=><Link key={s.id} href={`/communities/${s.id}`} className="px-4 py-2 rounded-full bg-white border border-slate-200 text-sm hover:border-[#0e7c7b]"><span className="font-semibold">{s.label}</span> <span className="text-slate-500">· {s.size} items</span></Link>)}
        </div>
      </div>

      <div className="mt-8 flex gap-3">
        <Link href="/analyze" className="bg-[#0e7c7b] text-white px-6 py-3 rounded-full font-semibold">Analyze an item like this</Link>
        <Link href="/discover" className="border border-slate-200 px-6 py-3 rounded-full font-semibold">View on map</Link>
      </div>
    </div>
  );
}
