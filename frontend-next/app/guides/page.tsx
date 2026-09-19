"use client";
import { useState } from "react";
import Link from "next/link";

const categories = [
  { id: "phone", label: "Phone", icon: "📱", do: ["Keep battery inside device", "Wipe personal data", "Keep screen intact"], dont: ["Don’t puncture battery", "Don’t throw in household trash"], next: "Drop at certified phone collection or retailer take-back." },
  { id: "laptop", label: "Laptop", icon: "💻", do: ["Back up and wipe drive", "Keep charger with device if possible"], dont: ["Don’t break screen or board", "Don’t store in damp place"], next: "Schedule pickup or bring to certified recycler." },
  { id: "battery", label: "Battery", icon: "🔋", do: ["Tape terminals", "Store dry and separate", "Use battery collection"], dont: ["Don’t crush or burn", "Don’t mix with general waste"], next: "Hand to battery-specific collection — coming soon: chemistry check." },
  { id: "pcb", label: "PCB", icon: "🟩", do: ["Keep board intact", "Handle by edges"], dont: ["Don’t burn or wash with water", "Don’t break into pieces"], next: "Route to e-waste recycler — coming soon: sub-category analysis." },
  { id: "charger", label: "Charger", icon: "🔌", do: ["Coil cable loosely", "Keep together"], dont: ["Don’t cut cable"], next: "Drop with small electronics." },
  { id: "monitor", label: "Monitor", icon: "🖥️", do: ["Keep screen unbroken", "Keep stand attached"], dont: ["Don’t crack glass"], next: "Use bulky-item pickup if available." },
  { id: "other", label: "Other", icon: "📦", do: ["Keep item dry and together"], dont: ["Don’t dismantle unsafely"], next: "Explore visual communities or ask your local collector." },
];

export default function GuidesPage() {
  const [active, setActive] = useState<string>("phone");
  const cat = categories.find((c) => c.id === active)!;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">What should I do with my electronic item?</h1>
      <p className="mt-2 text-slate-600">Choose a category — guidance is general and expandable. For hazardous items, follow local certified advice.</p>

      <div className="mt-6 flex flex-wrap gap-2">
        {categories.map((c) => (
          <button key={c.id} onClick={() => setActive(c.id)} className={`px-4 py-2 rounded-full border text-sm font-semibold ${active===c.id ? "bg-[#0e7c7b] text-white border-[#0e7c7b]" : "bg-white border-slate-200 hover:bg-slate-50"}`}>
            <span className="mr-1.5">{c.icon}</span>{c.label}
          </button>
        ))}
      </div>

      <div className="mt-8 grid lg:grid-cols-3 gap-6">
        <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-6">
          <h3 className="font-bold text-emerald-900">DO ✓</h3>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">{cat.do.map((d)=><li key={d}>✓ {d}</li>)}</ul>
        </div>
        <div className="rounded-2xl border border-red-100 bg-red-50 p-6">
          <h3 className="font-bold text-red-900">DON’T ✕</h3>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">{cat.dont.map((d)=><li key={d}>✕ {d}</li>)}</ul>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6">
          <h3 className="font-bold">NEXT STEP →</h3>
          <p className="mt-3 text-sm leading-6 text-slate-600">{cat.next}</p>
          <Link href="/learn" className="mt-4 inline-block text-sm font-semibold text-[#0e7c7b]">Learn more →</Link>
        </div>
      </div>

      <p className="mt-8 text-xs text-slate-400">Guidance is general. For batteries and damaged screens, consult certified local services. Future specialized classifiers (battery chemistry, PCB sub-type) will enhance this page — currently marked “Coming soon” where applicable.</p>
    </div>
  );
}
