import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Making e-waste easier to understand</h1>
      <p className="mt-3 text-lg leading-7 text-slate-600">Our platform combines visual AI and e-waste knowledge to help people better understand electronic items and explore more responsible handling pathways.</p>

      <div className="mt-8 grid sm:grid-cols-2 gap-5">
        {[
          { t: "Visual AI", d: "Finds visually similar items from thousands of images — no manual labels needed.", icon: "🤖" },
          { t: "E-Waste Education", d: "Plain-language guides on what e-waste is and how to handle it.", icon: "📚" },
          { t: "Visual Discovery", d: "Interactive map of 16 visual communities showing how items group together.", icon: "🗺️" },
          { t: "Circularity", d: "Connecting identification to recovery, reuse, and recycling pathways.", icon: "♻️" },
        ].map((c) => (
          <div key={c.t} className="rounded-3xl border border-slate-100 bg-slate-50 p-6">
            <div className="text-2xl">{c.icon}</div>
            <h3 className="mt-3 font-bold text-slate-900">{c.t}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{c.d}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 rounded-2xl border border-slate-200 bg-white p-6">
        <h2 className="font-bold">Our approach</h2>
        <p className="mt-2 text-sm leading-7 text-slate-600">We start from visual discovery (16 macro-communities from 3,637 images, SigLIP2), keep interpretations tentative, and layer education on top. Future specialized classifiers (battery type, PCB sub-category) will plug into the same visual groups — architecture is ready, but we don’t fake results today.</p>
      </div>

      <div className="mt-8 flex gap-3">
        <Link href="/analyze" className="bg-[#0e7c7b] text-white px-6 py-3 rounded-full font-semibold">Analyze an Item</Link>
        <Link href="/learn" className="border border-slate-200 px-6 py-3 rounded-full font-semibold">Explore Learning</Link>
      </div>
    </div>
  );
}
