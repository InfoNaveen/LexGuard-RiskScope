import { useState } from "react";
import { downloadReport } from "../lib/api.js";
import { getClauseType, getMaxRiskScore, normalizeSeverity, severityDots } from "../lib/risk.js";

const severities = ["critical", "high", "medium", "low"];

function getMostCommonClauseType(clauses) {
  const counts = clauses.reduce((accumulator, clause) => {
    const type = getClauseType(clause);
    accumulator[type] = (accumulator[type] || 0) + 1;
    return accumulator;
  }, {});

  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || "none";
}

export default function SummaryPanel({ jobId, clauses, totalClauses }) {
  const [downloadState, setDownloadState] = useState({ loading: false, error: "" });
  const severityCounts = severities.reduce((accumulator, severity) => {
    accumulator[severity] = clauses.filter((clause) => normalizeSeverity(clause.severity) === severity).length;
    return accumulator;
  }, {});
  const overallRisk = clauses.length
    ? clauses.reduce((total, clause) => total + getMaxRiskScore(clause), 0) / clauses.length
    : 0;
  const mostCommonType = getMostCommonClauseType(clauses);

  const handleDownload = async () => {
    try {
      setDownloadState({ loading: true, error: "" });
      await downloadReport(jobId);
      setDownloadState({ loading: false, error: "" });
    } catch (error) {
      setDownloadState({ loading: false, error: error.message || "Report download failed." });
    }
  };

  return (
    <aside className="rounded-lg bg-[#0f1117] p-6 text-white shadow-2xl">
      <p className="text-xs font-black uppercase tracking-[0.22em] text-slate-400">Final Report</p>
      <h2 className="mt-2 text-2xl font-black">Analysis Summary</h2>

      <div className="mt-6 grid gap-4">
        <div className="rounded-lg bg-white/5 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-slate-400">Total Clauses Analyzed</p>
          <p className="mt-2 text-3xl font-black">{totalClauses || clauses.length}</p>
        </div>

        <div className="rounded-lg bg-white/5 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-slate-400">Severity Counts</p>
          <div className="mt-3 flex flex-wrap gap-3">
            {severities.map((severity) => (
              <span key={severity} className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wide">
                <span className={`h-2.5 w-2.5 rounded-full ${severityDots[severity]}`} />
                {severity} {severityCounts[severity]}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-lg bg-white/5 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-slate-400">Overall Risk Score</p>
          <p className="mt-2 text-5xl font-black">{overallRisk.toFixed(1)} <span className="text-base text-slate-400">/ 10</span></p>
        </div>

        <div className="rounded-lg bg-white/5 p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-slate-400">Most Common Clause Type</p>
          <p className="mt-2 text-lg font-black capitalize">{mostCommonType.replaceAll("-", " ")}</p>
        </div>
      </div>

      <button
        type="button"
        onClick={handleDownload}
        disabled={downloadState.loading}
        className="mt-6 inline-flex h-11 w-full items-center justify-center rounded-md bg-[#185FA5] px-4 text-sm font-black text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-slate-600"
      >
        {downloadState.loading ? "Downloading..." : "Download Report"}
      </button>

      {downloadState.error ? <p className="mt-3 text-sm font-semibold text-red-200">{downloadState.error}</p> : null}
    </aside>
  );
}
