import Link from "next/link";
import { articles } from "@/lib/articles";

export default function LearnPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">E-Waste Learning Center</h1>
      <p className="mt-2 text-slate-600 max-w-2xl">Simple guides to help you understand, handle, and recycle electronic waste responsibly.</p>

      <div className="mt-8 grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {articles.map((a) => (
          <Link key={a.slug} href={`/learn/${a.slug}`} className="rounded-3xl border border-slate-100 bg-white p-6 hover:shadow-md transition flex flex-col">
            <h3 className="font-bold text-slate-900">{a.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600 flex-1">{a.excerpt}</p>
            <div className="mt-4 text-sm font-semibold text-[#0e7c7b]">Read more →</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
