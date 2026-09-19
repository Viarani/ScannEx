import Link from "next/link";

export default function Home() {
  return (
    <div>
      {/* HERO */}
      <section className="relative overflow-hidden bg-gradient-to-b from-sky-50 via-white to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20 grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <p className="text-xs font-bold tracking-[0.2em] text-[#0e7c7b]">AI-POWERED E-WASTE INTELLIGENCE</p>
            <h1 className="mt-3 text-4xl sm:text-5xl lg:text-[48px] font-extrabold leading-[1.05] tracking-tight text-slate-900">
              Give your old electronics <br />
              <span className="text-[#0e7c7b]">a second look.</span>
            </h1>
            <p className="mt-5 text-lg leading-7 text-slate-600 max-w-xl">
              Use AI to recognize electronic items and discover how they can be handled, recovered, or recycled more responsibly.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/analyze" className="bg-[#0e7c7b] text-white px-7 py-3.5 rounded-full font-semibold hover:bg-[#0a5e5d] transition">
                Analyze an Item
              </Link>
              <Link href="/learn" className="border-2 border-slate-200 px-7 py-3 rounded-full font-semibold hover:border-slate-300 hover:bg-slate-50 transition">
                Learn About E-Waste
              </Link>
            </div>
            <p className="mt-6 text-xs text-slate-500">Works with your camera · No technical knowledge needed</p>
          </div>

          {/* Hero visual — use modern photo placeholder */}
          <div className="relative">
            <div className="relative rounded-[32px] overflow-hidden bg-slate-900 shadow-2xl aspect-[4/3] lg:aspect-[1.1/1]">
              {/* Replace src with your own hero photo: /public/hero-ewaste.jpg */}
              <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-700 to-teal-900" />
              <div className="absolute inset-0 opacity-40 bg-[radial-gradient(600px_400px_at_30%_20%,rgba(255,255,255,0.15),transparent_70%)]" />
              <div className="absolute inset-0 flex items-center justify-center p-8">
                <div className="relative w-full max-w-[360px] bg-white rounded-3xl p-5 shadow-xl">
                  <div className="flex items-center gap-2 text-xs font-bold tracking-wide text-slate-500">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> LIVE CAMERA
                  </div>
                  <div className="mt-4 aspect-[4/3] rounded-2xl bg-slate-100 border-2 border-dashed border-slate-200 grid place-items-center overflow-hidden relative">
                    <div className="absolute inset-4 border-2 border-[#0e7c7b]/60 rounded-xl" />
                    <div className="absolute inset-4 border border-white/60 rounded-xl" />
                    <div className="text-center">
                      <div className="text-4xl">📱</div>
                      <p className="mt-2 text-xs text-slate-500">Point at an electronic item</p>
                    </div>
                  </div>
                  <div className="mt-4 flex justify-center">
                    <span className="bg-[#0e7c7b] text-white px-6 py-2 rounded-full text-sm font-semibold">Scan Item</span>
                  </div>
                </div>
              </div>
              <div className="absolute bottom-4 left-4 right-4 bg-white/95 backdrop-blur rounded-2xl p-4 flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-teal-50 grid place-items-center text-[#0e7c7b]">♻</div>
                <div>
                  <div className="text-sm font-semibold text-slate-900">Visual match found</div>
                  <div className="text-xs text-slate-500">Computer peripheral group · Explore similar items</div>
                </div>
              </div>
            </div>
            <div className="absolute -z-10 -bottom-6 -right-6 w-72 h-72 bg-teal-100 rounded-full blur-3xl opacity-40" />
            <div className="absolute -z-10 -top-6 -left-6 w-64 h-64 bg-sky-100 rounded-full blur-3xl opacity-40" />
          </div>
        </div>
      </section>

      {/* SECTION 1 — What can you discover? */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-xs font-bold tracking-[0.2em] text-[#0e7c7b]">EXPLORE EXAMPLES</p>
          <div className="mt-3 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
            <h2 className="text-3xl font-extrabold text-slate-900">What can you discover?</h2>
            <p className="text-sm text-slate-500 max-w-md">Examples of electronic items our visual system has learned to group. Explore different electronic items — interpretations are tentative.</p>
          </div>
          <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-5 gap-5">
            {[
              { t: "Computers", d: "Desktops, laptops, and towers", icon: "💻" },
              { t: "Mobile Devices", d: "Phones and tablets", icon: "📱" },
              { t: "Batteries", d: "Lithium and household cells", icon: "🔋" },
              { t: "Circuit Boards", d: "PCBs and recovery potential", icon: "🟩" },
              { t: "Electronics & Peripherals", d: "Keyboards, mice, printers", icon: "⌨️" },
            ].map((c) => (
              <div key={c.t} className="rounded-2xl border border-slate-100 bg-slate-50/60 p-5 hover:shadow-md transition">
                <div className="w-12 h-12 rounded-2xl bg-white border border-slate-100 grid place-items-center text-xl">{c.icon}</div>
                <h3 className="mt-4 font-bold text-slate-900">{c.t}</h3>
                <p className="mt-1 text-sm text-slate-600 leading-6">{c.d}</p>
                <div className="mt-4 text-xs font-semibold text-[#0e7c7b]">Explore →</div>
              </div>
            ))}
          </div>
          <div className="mt-6 text-center">
            <Link href="/communities" className="inline-flex text-sm font-semibold text-[#0e7c7b] hover:underline">
              View all 16 visual communities →
            </Link>
          </div>
        </div>
      </section>

      {/* SECTION 2 — From camera to insight */}
      <section className="py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-xs font-bold tracking-[0.2em] text-[#0e7c7b]">HOW IT WORKS</p>
          <h2 className="mt-3 text-3xl font-extrabold text-slate-900">From camera to insight</h2>
          <div className="mt-10 grid md:grid-cols-3 gap-6">
            {[
              { n: "01", t: "Show your item", d: "Use your live camera or upload a photo. No names or categories needed.", icon: "📷" },
              { n: "02", t: "Let AI analyze it", d: "We find visually similar items from thousands of electronic images.", icon: "✨" },
              { n: "03", t: "Explore the result", d: "See your visual match, similar items, and what to do next.", icon: "🔍" },
            ].map((s) => (
              <div key={s.n} className="bg-white rounded-3xl p-8 border border-slate-100">
                <div className="text-3xl">{s.icon}</div>
                <div className="mt-4 text-xs font-bold tracking-widest text-[#0e7c7b]">{s.n}</div>
                <h3 className="mt-1 text-lg font-bold text-slate-900">{s.t}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 3 — E-Waste Learning */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row justify-between gap-4 items-start">
            <div>
              <p className="text-xs font-bold tracking-[0.2em] text-[#0e7c7b]">E-WASTE LEARNING</p>
              <h2 className="mt-3 text-3xl font-extrabold text-slate-900">Learn the essentials</h2>
            </div>
            <Link href="/learn" className="text-sm font-semibold text-[#0e7c7b] hover:underline shrink-0">
              Browse learning center →
            </Link>
          </div>
          <div className="mt-8 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { t: "Understanding E-Waste", d: "What e-waste is, what’s inside, and why it matters.", slug: "understanding-e-waste" },
              { t: "Why Recycling Matters", d: "Environmental and community benefits of responsible recycling.", slug: "why-recycling-matters" },
              { t: "Your Role & Community", d: "How individuals and communities contribute to circularity.", slug: "your-role-and-community" },
              { t: "Safe E-Waste Handling", d: "Storing and handling items safely before collection.", slug: "safe-ewaste-handling" },
            ].map((a) => (
              <Link key={a.slug} href={`/learn/${a.slug}`} className="rounded-2xl border border-slate-100 p-6 hover:shadow-md transition bg-white">
                <h3 className="font-bold text-slate-900">{a.t}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{a.d}</p>
                <div className="mt-4 text-sm font-semibold text-[#0e7c7b]">Read more →</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 4 — CTA */}
      <section className="py-16 bg-[#0e2f2e] text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(800px_400px_at_70%_30%,white,transparent)]" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold">Have an electronic item you’re unsure about?</h2>
          <p className="mt-3 text-teal-100 text-lg">Let AI help you take a closer look.</p>
          <div className="mt-8">
            <Link href="/analyze" className="inline-flex bg-white text-[#0e2f2e] px-8 py-3.5 rounded-full font-bold hover:bg-teal-50 transition">
              Analyze an Item
            </Link>
            <div className="mt-3 text-sm text-teal-200">Works with camera or photo upload · No signup needed</div>
          </div>
        </div>
      </section>
    </div>
  );
}
