import { useState } from 'react';
import { 
  ArrowLeftRight, 
  ShieldCheck, 
  RotateCcw, 
  Wifi, 
  UploadCloud, 
  FileText 
} from 'lucide-react';
import { formatBytes } from './utils/formatters';

export function App() {
  const [roomId, setRoomId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-600 rounded-lg">
            <ArrowLeftRight className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">P2P Transfer</h1>
            <p className="text-xs text-slate-400">Direct WebRTC & Resumable File Streaming</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-full">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
          <span>Ready to connect</span>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-6 space-y-6">
        {/* Core Value Props */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 flex items-start gap-3">
            <Wifi className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold">Easy Connection</h3>
              <p className="text-xs text-slate-400 mt-1">
                Fast room codes, QR pairing, and instant WebRTC peer discovery.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 flex items-start gap-3">
            <RotateCcw className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold">Resumable Transfers</h3>
              <p className="text-xs text-slate-400 mt-1">
                Chunked streaming with offset tracking. Never restart from scratch.
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold">Direct & Secure</h3>
              <p className="text-xs text-slate-400 mt-1">
                End-to-end peer encrypted transfers without intermediary cloud storage.
              </p>
            </div>
          </div>
        </div>

        {/* Pairing Card */}
        <section className="p-6 rounded-2xl border border-slate-800 bg-slate-900/50 space-y-4">
          <h2 className="text-base font-semibold">1. Pair with Peer</h2>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={roomId}
              onChange={(e) => setRoomId(e.target.value.toUpperCase())}
              placeholder="Enter 6-character room code..."
              className="flex-1 px-4 py-2.5 rounded-lg bg-slate-950 border border-slate-700 text-sm focus:outline-none focus:border-indigo-500 font-mono tracking-widest placeholder:tracking-normal placeholder:font-sans"
              maxLength={8}
            />
            <button className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition cursor-pointer">
              Join Room
            </button>
            <button className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm font-medium transition cursor-pointer">
              Create New Room
            </button>
          </div>
        </section>

        {/* File Dropzone */}
        <section className="p-8 rounded-2xl border border-dashed border-slate-700 hover:border-indigo-500/70 bg-slate-900/30 transition flex flex-col items-center justify-center text-center cursor-pointer">
          <UploadCloud className="w-12 h-12 text-slate-400 mb-3" />
          <h3 className="text-sm font-medium">Drag & drop files here, or click to browse</h3>
          <p className="text-xs text-slate-500 mt-1">Supports any file size. Transferred in resumable binary chunks.</p>
          <input
            type="file"
            className="hidden"
            id="file-upload"
            onChange={(e) => {
              if (e.target.files?.[0]) setSelectedFile(e.target.files[0]);
            }}
          />
          <label
            htmlFor="file-upload"
            className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-medium cursor-pointer border border-slate-700"
          >
            Select File
          </label>

          {selectedFile && (
            <div className="mt-4 p-3 bg-slate-800/80 rounded-lg border border-slate-700 flex items-center gap-3 text-left">
              <FileText className="w-6 h-6 text-indigo-400 shrink-0" />
              <div>
                <p className="text-xs font-semibold text-slate-200">{selectedFile.name}</p>
                <p className="text-[11px] text-slate-400">{formatBytes(selectedFile.size)}</p>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-4 px-6 text-center text-xs text-slate-500">
        P2P Transfer · WebRTC DataChannel & FastAPI Signaling
      </footer>
    </div>
  );
}

export default App;
