"use client";
import { useRef, useState } from "react";
import { Upload } from "lucide-react";

export default function FileDrop({ onFile, accept = ".pdf,.docx,.txt", label = "Drop or click to upload" }:
  { onFile: (f: File) => void; accept?: string; label?: string }) {
  const ref = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault(); setOver(false);
        const f = e.dataTransfer.files?.[0]; if (f) onFile(f);
      }}
      onClick={() => ref.current?.click()}
      className={`card p-8 text-center cursor-pointer ${over ? "ring-2 ring-brand-500" : ""}`}
    >
      <Upload className="mx-auto mb-2" />
      <div className="font-medium">{label}</div>
      <div className="text-xs opacity-70 mt-1">PDF, DOCX, TXT</div>
      <input ref={ref} type="file" accept={accept} className="hidden"
             onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }} />
    </div>
  );
}
