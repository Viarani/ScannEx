"use client";
import { useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:5000";

export default function AnalyzePage() {
  const router = useRouter();
  const [mode, setMode] = useState<"camera" | "upload">("camera");
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [streamOn, setStreamOn] = useState(false);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    return () => stopCamera();
  }, []);

  async function startCamera() {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      if (videoRef.current) {
        videoRef.current.srcObject = s;
        await videoRef.current.play();
        setStreamOn(true);
        setStatus("");
      }
    } catch (e: any) {
      setStatus("Camera access denied or unavailable. Please try upload instead. (" + (e?.message || "") + ")");
    }
  }
  function stopCamera() {
    const v = videoRef.current;
    if (v?.srcObject) {
      (v.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
      v.srcObject = null;
    }
    setStreamOn(false);
  }

  async function sendBlob(blob: Blob) {
    setBusy(true);
    setStatus("Analyzing your item...");
    const fd = new FormData();
    fd.append("image", blob, "capture.jpg");
    try {
      const r = await fetch(`${API_URL}/api/predict`, { method: "POST", body: fd });
      const text = await r.text();
      let j: any;
      try { j = JSON.parse(text); } catch { throw new Error(text.slice(0,300)); }
      if (!r.ok) throw new Error(j.error || j.hint || "Analysis failed");
      // also fetch sizes for friendly names? backend already returns names map
      // store result for /result page
      const toStore = { ...j, uploadedPreview: preview || undefined, timestamp: Date.now() };
      // also store preview blob url? use preview state
      sessionStorage.setItem("ewaste_last_result", JSON.stringify(toStore));
      // store preview image as data url separately if we have blob
      if (blob) {
        const reader = new FileReader();
        reader.onload = () => {
          try { sessionStorage.setItem("ewaste_preview", reader.result as string); } catch {}
          router.push("/result");
        };
        reader.readAsDataURL(blob);
      } else {
        router.push("/result");
      }
    } catch (e: any) {
      setStatus("Analysis failed: " + String(e.message || e) + " — please try again with a clearer photo.");
      setBusy(false);
    }
  }

  function capture() {
    if (!videoRef.current || !canvasRef.current) return;
    const v = videoRef.current, c = canvasRef.current;
    c.width = v.videoWidth; c.height = v.videoHeight;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0);
    // set preview
    const dataUrl = c.toDataURL("image/jpeg", 0.9);
    setPreview(dataUrl);
    c.toBlob((b) => b && sendBlob(b), "image/jpeg", 0.9);
  }

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const url = URL.createObjectURL(f);
    setPreview(url);
    sendBlob(f);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (!f) return;
    const url = URL.createObjectURL(f);
    setPreview(url);
    sendBlob(f);
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">Identify your electronic item</h1>
        <p className="mt-3 text-slate-600">Use your camera or upload an image to explore what you&apos;re looking at.</p>
      </div>

      <div className="mt-8 flex justify-center gap-3">
        <button onClick={() => { setMode("camera"); setStatus(""); }} className={`px-6 py-2.5 rounded-full font-semibold border ${mode==="camera" ? "bg-[#0e7c7b] text-white border-[#0e7c7b]" : "bg-white border-slate-200 text-slate-700"}`}>Use Camera</button>
        <button onClick={() => { setMode("upload"); stopCamera(); setStatus(""); }} className={`px-6 py-2.5 rounded-full font-semibold border ${mode==="upload" ? "bg-[#0e7c7b] text-white border-[#0e7c7b]" : "bg-white border-slate-200 text-slate-700"}`}>Upload Image</button>
      </div>

      <div className="mt-8 max-w-3xl mx-auto">
        {mode === "camera" ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-4 sm:p-6">
            <div className="relative aspect-[4/3] bg-slate-900 rounded-2xl overflow-hidden grid place-items-center">
              <video ref={videoRef} playsInline muted className={`w-full h-full object-cover ${streamOn ? "" : "hidden"}`} />
              {!streamOn && <div className="text-slate-400 text-sm">Camera preview will appear here</div>}
              {/* scanning frame overlay */}
              <div className={`absolute inset-0 pointer-events-none ${streamOn ? "" : "hidden"}`}>
                <div className="absolute inset-6 sm:inset-10 border-2 border-white/80 rounded-2xl" />
                <div className="absolute inset-6 sm:inset-10 border border-[#0e7c7b]/50 rounded-2xl" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 border-2 border-white rounded-xl opacity-60" />
                <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-black/60 text-white text-xs px-3 py-1 rounded-full backdrop-blur">LIVE CAMERA</div>
              </div>
              <canvas ref={canvasRef} className="hidden" />
            </div>

            <div className="mt-6 flex flex-wrap justify-center gap-3">
              {!streamOn ? (
                <button onClick={startCamera} className="bg-[#0e7c7b] text-white px-7 py-3 rounded-full font-semibold hover:bg-[#0a5e5d]">Enable Camera</button>
              ) : (
                <>
                  <button onClick={capture} disabled={busy} className="bg-[#0e7c7b] text-white px-8 py-3 rounded-full font-semibold disabled:opacity-50 hover:bg-[#0a5e5d]">
                    {busy ? "Analyzing..." : "Scan Item"}
                  </button>
                  <button onClick={stopCamera} className="border border-slate-200 px-6 py-3 rounded-full font-semibold bg-white">Stop Camera</button>
                </>
              )}
            </div>
            {preview && (
              <div className="mt-6">
                <p className="text-sm font-semibold text-slate-700">Preview</p>
                <img src={preview} alt="preview" className="mt-2 w-full max-w-sm mx-auto rounded-xl border" />
              </div>
            )}
            {status && <p className="mt-4 text-center text-sm text-slate-600">{status}</p>}
            <p className="mt-4 text-center text-xs text-slate-400">Your camera stays on-device until you tap Scan. We only send the captured frame.</p>
          </div>
        ) : (
          <div className="rounded-3xl border border-slate-200 bg-white p-6">
            <div onDragOver={(e)=>e.preventDefault()} onDrop={onDrop} className="rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center hover:border-[#0e7c7b]/50 transition">
              <div className="mx-auto w-12 h-12 rounded-2xl bg-white border border-slate-200 grid place-items-center text-xl">🖼️</div>
              <p className="mt-3 font-semibold text-slate-900">Drop an electronic item image here</p>
              <p className="text-sm text-slate-500">or</p>
              <label className="mt-3 inline-flex bg-[#0e7c7b] text-white px-6 py-2.5 rounded-full font-semibold cursor-pointer hover:bg-[#0a5e5d]">
                Choose Image
                <input ref={fileRef} type="file" accept=".jpg,.jpeg,.png,.webp" onChange={onFile} className="hidden" />
              </label>
              <p className="mt-3 text-xs text-slate-400">JPG, JPEG, PNG, WEBP — max 16MB</p>
            </div>
            {preview && (
              <div className="mt-6 text-center">
                <img src={preview} alt="preview" className="mx-auto max-w-sm rounded-xl border" />
                <p className="mt-3 text-sm text-slate-600">{busy ? "Analyzing..." : "Ready to analyze"}</p>
                {!busy && <p className="text-xs text-slate-400">If preview looks wrong, choose another image.</p>}
              </div>
            )}
            {status && <p className="mt-4 text-center text-sm text-slate-600">{status}</p>}
          </div>
        )}
      </div>

      <p className="mt-8 text-center text-xs text-slate-400">By analyzing, you agree we process the image to find visually similar items. No personal data is stored.</p>
    </div>
  );
}
