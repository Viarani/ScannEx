"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const nav = [
  { href: "/", label: "Home" },
  { href: "/analyze", label: "Analyze" },
  { href: "/discover", label: "Discover" },
  { href: "/learn", label: "Learn" },
  { href: "/guides", label: "Guides" },
  { href: "/about", label: "About" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-[64px] flex items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-2 font-extrabold text-lg tracking-tight text-slate-900">
          <span className="w-8 h-8 rounded-full bg-[#0e7c7b] grid place-items-center text-white text-sm">♻</span>
          E-Waste<span className="text-[#0e7c7b]"> Intelligence</span>
        </Link>

        <nav className="hidden md:flex items-center gap-7 text-[14px] font-medium text-slate-700">
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={`${pathname === n.href ? "text-[#0e7c7b]" : "hover:text-[#0e7c7b]"} transition`}
            >
              {n.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center">
          <Link href="/analyze" className="bg-[#0e7c7b] text-white px-5 py-2.5 rounded-full text-sm font-semibold hover:bg-[#0a5e5d] transition">
            Analyze an Item
          </Link>
        </div>

        <button onClick={() => setOpen(!open)} className="md:hidden p-2 rounded-lg border border-slate-200" aria-label="menu">
          <span className="block w-5 h-0.5 bg-slate-700 mb-1.5" />
          <span className="block w-5 h-0.5 bg-slate-700 mb-1.5" />
          <span className="block w-5 h-0.5 bg-slate-700" />
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-slate-100 bg-white">
          <nav className="px-4 py-4 flex flex-col gap-3 text-sm font-medium">
            {nav.map((n) => (
              <Link key={n.href} href={n.href} onClick={() => setOpen(false)} className={pathname === n.href ? "text-[#0e7c7b]" : ""}>
                {n.label}
              </Link>
            ))}
            <Link href="/analyze" onClick={() => setOpen(false)} className="mt-2 bg-[#0e7c7b] text-white px-5 py-3 rounded-full text-center font-semibold">
              Analyze an Item
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
