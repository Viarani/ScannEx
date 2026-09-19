"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

type Result = any;

export default function ResultPage() {
  const [result, setResult] = useState<Result | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    try {
      const r = sessionStorage.getItem("ewaste_last_result");
      const p = sessionStorage.getItem("ewaste_preview");
      if (r) setResult(JSON.parse(r));
      if (p) setPreview(p);
    } catch {}
  }, []);

  if (!result) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h1 className="text-2xl font-extrabold text-slate-900">No analysis yet</h1>
        <p className="mt-2 text-slate-600">Analyze an item with your camera or upload a photo to see results here.</p>
        <Link href="/analyze" className="mt-6 inline-flex bg-[#0e7c7b] text-white px-7 py-3 rounded-full font-semibold">Analyze an Item</Link>
      </div>
    );
  }

  const isAmbiguous = result.interpretation?.toLowerCase().includes("mixed") || result.interpretation?.toLowerCase().includes("ambiguous") || result.neighbour_agreement_pct < 55;
  const heading = isAmbiguous ? "We found a visually similar group" : result.interpretation || "Electronic device";
  const sub = isAmbiguous ? "Similar electronic item" : "Visual match";

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="grid lg:grid-cols-2 gap-8 items-start">
        <div className="rounded-3xl border border-slate-200 bg-white p-4">
          <div className="aspect-[4/3] rounded-2xl overflow-hidden bg-slate-100 grid place-items-center">
            {preview ? <img src={preview} alt="analyzed" className="w-full h-full object-contain" /> : <span className="text-slate-400 text-sm">Your image</span>}
          </div>
          <p className="mt-3 text-xs text-slate-500 text-center">Analyzed image · Visual identification only</p>
        </div>

        <div>
          <p className="text-xs font-bold tracking-[0.2em] text-[#0e7c7b]">WE FOUND SOMETHING</p>
          <h1 className="mt-2 text-3xl font-extrabold text-slate-900">{heading}</h1>
          <p className="mt-1 text-slate-600">{isAmbiguous ? "This represents a visual identification — it groups items that look alike." : "Electronic device"}</p>

          <div className="mt-6 rounded-2xl bg-slate-50 border border-slate-100 p-5">
            <p className="text-xs font-bold tracking-wide text-slate-500">VISUAL MATCH</p>
            <p className="mt-1 font-semibold text-slate-900">{result.interpretation}</p>
            <p className="text-sm text-slate-600">Tentative visual interpretation · {result.size} visual items · {result.share_pct}% of dataset</p>
            <p className="mt-2 text-sm text-slate-600">
              <span className="font-semibold">{result.neighbour_agreement_pct != null ? `Neighbour agreement: ${result.neighbour_agreement_pct}%` : "Visual match"}</span>
              <span className="text-slate-500"> {result.coherence ? `· ${result.coherence}` : ""}</span>
            </p>
            {isAmbiguous && <p className="mt-2 text-xs text-slate-500">We avoid forcing a specific name when the visual group is mixed. This is a visually similar collection, not a definitive label.</p>}
          </div>

          <div className="mt-6">
            <h3 className="font-bold text-slate-900">About this item</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {result.interpretation?.includes("Battery") ? "Batteries contain materials that need careful handling. Keep them dry and separate from other waste." :
                result.interpretation?.includes("PCB") ? "Circuit boards often contain recoverable metals. Handling should avoid breaking or burning." :
                result.interpretation?.includes("Washing") || result.interpretation?.includes("Microwave") ? "Large appliances are bulky and often collected via dedicated pickup services." :
                "Electronic items vary in materials and handling needs. Exploring similar items can help you decide the next step."}
            </p>
          </div>

          <div className="mt-6 rounded-2xl bg-white border border-slate-200 p-5">
            <h3 className="font-bold">What you can do next</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li><Link href="/learn" className="text-[#0e7c7b] font-semibold hover:underline">Learn more about this type of e-waste →</Link></li>
              <li><Link href="/guides" className="text-[#0e7c7b] font-semibold hover:underline">View handling guide →</Link></li>
              <li><Link href="/communities" className="text-[#0e7c7b] font-semibold hover:underline">Explore similar visual groups →</Link></li>
            </ul>
          </div>
        </div>
      </div>

      <div className="mt-10">
        <h2 className="text-lg font-extrabold text-slate-900">Explore similar items</h2>
        <p className="text-sm text-slate-500">Visually matched from our reference collection — not a purchase list.</p>
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {(result.top5 || []).map((t: any) => (
            <div key={t.index} className="rounded-2xl border border-slate-100 overflow-hidden bg-white">
              <div className="aspect-square bg-slate-100 grid place-items-center text-xs text-slate-500 p-2 text-center">
                {t.filename}
              </div>
              <div className="p-3">
                <div className="text-xs font-semibold text-slate-700 truncate">{result.names?.[String(t.community)] || "Visual group"}</div>
                <div className="text-xs text-slate-500">Strong visual match</div>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-400">We show filename placeholders here; with Flask static serving you can replace with real thumbnails from /static/communities or representative images.</p>
      </div>

      <div className="mt-10 flex flex-wrap gap-3">
        <Link href="/analyze" className="bg-[#0e7c7b] text-white px-6 py-3 rounded-full font-semibold">Analyze another item</Link>
        <Link href="/guides" className="border border-slate-200 px-6 py-3 rounded-full font-semibold hover:bg-slate-50">See handling guide</Link>
      </div>
    </div>
  );
}
