import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { startAnalysis, uploadContract } from "../lib/api.js";

function formatFileSize(bytes) {
  if (!bytes) {
    return "0 KB";
  }

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** index;
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[index]}`;
}

function isPdfOrDocx(file) {
  const extension = file.name.split(".").pop()?.toLowerCase();
  return extension === "pdf" || extension === "docx";
}

function Spinner() {
  return (
    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" aria-hidden="true" />
  );
}

export default function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [inlineError, setInlineError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const chooseFile = (nextFile) => {
    setInlineError("");
    setSubmitError("");

    if (!nextFile) {
      setFile(null);
      return;
    }

    if (!isPdfOrDocx(nextFile)) {
      setFile(null);
      setInlineError("Only PDF and DOCX contracts are accepted.");
      return;
    }

    setFile(nextFile);
  };

  const submit = async () => {
    if (!file) {
      setInlineError("Select a PDF or DOCX contract before uploading.");
      return;
    }

    try {
      setIsUploading(true);
      setInlineError("");
      setSubmitError("");

      const uploadResult = await uploadContract(file);
      const jobId = uploadResult?.job_id;

      if (!jobId) {
        throw new Error("Upload completed without a job_id.");
      }

      await startAnalysis(jobId);
      navigate(`/analyze/${encodeURIComponent(jobId)}`);
    } catch (error) {
      setSubmitError(error.message || "Upload failed. Please retry.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white">
      <div className="grid min-h-screen lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="bg-[#0f1117] px-8 py-10 text-white">
          <p className="text-xs font-black uppercase tracking-[0.25em] text-slate-400">LexGuard</p>
          <h1 className="mt-3 text-4xl font-black leading-tight">RiskScope</h1>
          <p className="mt-5 text-sm leading-6 text-slate-300">
            Security-grade contract intelligence with adversarial legal analysis and negotiation guidance.
          </p>
          <div className="mt-10 rounded-lg border border-white/10 bg-white/5 p-4">
            <p className="text-xs font-black uppercase tracking-wide text-slate-400">Intake</p>
            <p className="mt-2 text-sm font-semibold text-slate-200">PDF or DOCX contract files</p>
          </div>
        </aside>

        <section className="flex items-center justify-center px-6 py-12">
          <div className="w-full max-w-3xl">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-[#185FA5]">Contract Upload</p>
            <h2 className="mt-2 text-3xl font-black text-slate-950">Start an analysis run</h2>

            <div
              onDragOver={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setIsDragging(false);
                chooseFile(event.dataTransfer.files?.[0]);
              }}
              className={`mt-8 rounded-lg border-2 border-dashed p-12 transition ${
                isDragging ? "border-[#185FA5] bg-blue-50" : "border-slate-300 bg-slate-50"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(event) => chooseFile(event.target.files?.[0])}
                className="sr-only"
              />

              <div className="flex flex-col items-center text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-[#0f1117] text-xl font-black text-white">
                  LG
                </div>
                <h3 className="mt-5 text-xl font-black text-slate-950">Drop contract here</h3>
                <p className="mt-2 text-sm text-slate-500">The pipeline extracts the contract, then RiskScope starts analysis.</p>
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="mt-6 inline-flex h-11 items-center justify-center rounded-md border border-slate-300 bg-white px-4 text-sm font-black text-slate-900 shadow-sm transition hover:bg-slate-100"
                >
                  Browse Files
                </button>
              </div>
            </div>

            {inlineError ? <p className="mt-4 text-sm font-semibold text-[#A32D2D]">{inlineError}</p> : null}

            {file ? (
              <div className="mt-5 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                <div>
                  <p className="text-sm font-black text-slate-950">{file.name}</p>
                  <p className="mt-1 text-xs font-bold uppercase tracking-wide text-slate-500">{formatFileSize(file.size)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => chooseFile(null)}
                  className="rounded-md border border-slate-300 px-3 py-2 text-xs font-black uppercase tracking-wide text-slate-600 hover:bg-slate-50"
                >
                  Remove
                </button>
              </div>
            ) : null}

            {submitError ? (
              <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm font-semibold text-[#A32D2D]">{submitError}</p>
                <button
                  type="button"
                  onClick={submit}
                  disabled={!file || isUploading}
                  className="mt-3 inline-flex h-10 items-center justify-center rounded-md bg-[#A32D2D] px-4 text-sm font-black text-white transition hover:bg-red-900 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  Retry
                </button>
              </div>
            ) : null}

            <button
              type="button"
              onClick={submit}
              disabled={!file || isUploading}
              className="mt-6 inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-[#185FA5] px-5 text-sm font-black uppercase tracking-wide text-white shadow-sm transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-300 sm:w-auto"
            >
              {isUploading ? <Spinner /> : null}
              {isUploading ? "Uploading" : "Upload And Analyze"}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
