import { notFound } from "next/navigation";
import Link from "next/link";
import { articles, getArticle } from "@/lib/articles";

export function generateStaticParams() {
  return articles.map((a) => ({ slug: a.slug }));
}

export default function ArticleDetail({ params }: { params: { slug: string } }) {
  const article = getArticle(params.slug);
  if (!article) return notFound();
  const idx = articles.findIndex((a) => a.slug === params.slug);
  const prev = idx > 0 ? articles[idx - 1] : null;
  const next = idx < articles.length - 1 ? articles[idx + 1] : null;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <Link href="/learn" className="text-sm text-slate-500 hover:text-slate-700">← Learning Center</Link>
      <h1 className="mt-4 text-3xl font-extrabold tracking-tight text-slate-900">{article.title}</h1>
      <p className="mt-2 text-slate-600">{article.excerpt}</p>

      <div className="mt-8 space-y-8">
        {article.sections.map((s, i) => (
          <div key={i} className="rounded-2xl bg-slate-50 border border-slate-100 p-6">
            <div className="text-xs font-bold tracking-widest text-[#0e7c7b]">0{i + 1}</div>
            <h2 className="mt-1 text-lg font-bold text-slate-900">{s.heading}</h2>
            <p className="mt-2 text-sm leading-7 text-slate-600">{s.body}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 flex justify-between gap-4 border-t border-slate-100 pt-6">
        {prev ? <Link href={`/learn/${prev.slug}`} className="text-sm font-semibold text-[#0e7c7b]">← {prev.title}</Link> : <span />}
        {next ? <Link href={`/learn/${next.slug}`} className="text-sm font-semibold text-[#0e7c7b]">{next.title} →</Link> : <span />}
      </div>

      <div className="mt-10 rounded-2xl bg-[#0e7c7b] text-white p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <div className="font-bold">Have an item to check?</div>
          <div className="text-sm text-teal-100">Use your camera to identify it.</div>
        </div>
        <Link href="/analyze" className="bg-white text-[#0e7c7b] px-6 py-2.5 rounded-full font-bold">Analyze an Item</Link>
      </div>
    </div>
  );
}
