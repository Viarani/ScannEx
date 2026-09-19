import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "E-Waste Intelligence — Give your old electronics a second look",
  description:
    "Use AI to recognize electronic items and discover how they can be handled, recovered, or recycled more responsibly.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-white text-slate-800 antialiased">
        <Navbar />
        <main className="min-h-[60vh]">{children}</main>
        <footer className="border-t border-slate-100 bg-slate-50/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col md:flex-row justify-between gap-6 text-sm text-slate-500">
            <div>
              <div className="font-extrabold text-slate-900 flex items-center gap-2">
                <span className="w-7 h-7 rounded-full bg-[#0e7c7b] grid place-items-center text-white text-xs">♻</span>
                E-Waste Intelligence
              </div>
              <p className="mt-2 max-w-md leading-6">Making e-waste easier to understand through visual AI, education, and responsible handling pathways.</p>
            </div>
            <div className="text-xs leading-6">
              <div>© {new Date().getFullYear()} E-Waste Intelligence</div>
              <div>16 visual communities · 3,637 images · Visual AI for circularity</div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
