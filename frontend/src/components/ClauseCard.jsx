import { useState } from "react";
import {
  clauseTypeStyles,
  getClauseText,
  getClauseType,
  getRiskBarColor,
  getRiskValue,
  normalizeSeverity,
  RISK_AXES,
  severityStyles,
} from "../lib/risk.js";

function GavelIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 flex-none">
      <path d="M13.7 4.1 20 10.4l-2.2 2.2-6.3-6.3 2.2-2.2Z" fill="currentColor" />
      <path d="m5.1 10.6 2.2-2.2 6.3 6.3-2.2 2.2-6.3-6.3Z" fill="currentColor" opacity="0.72" />
      <path d="m13.8 15.5 5.3 5.3" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M3.5 20h8" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

export default function ClauseCard({ clause }) {
  const [expanded, setExpanded] = useState(false);
  const clauseType = getClauseType(clause);
  const severity = normalizeSeverity(clause.severity);
  const clauseText = getClauseText(clause);

  return (
    <article className="rounded-lg border border-slate-200 bg-white shadow-audit">
      <div className="px-6 py-5">
        <div className="flex items-center justify-between gap-4">
          <span className={`rounded-full border px-3 py-1 text-xs font-black uppercase tracking-wide ${clauseTypeStyles[clauseType] || clauseTypeStyles.other}`}>
            {clauseType.replaceAll("-", " ")}
          </span>
          <span className={`rounded border px-3 py-1 text-xs font-black uppercase tracking-wide ${severityStyles[severity]}`}>
            {severity}
          </span>
        </div>

        <p className="mt-5 text-sm leading-6 text-slate-500">
          {clause.plain_language_summary || "Plain-language summary unavailable."}
        </p>

        <div className="mt-5 border-l-4 border-slate-200 pl-4">
          <p className={`text-sm leading-6 text-slate-800 ${expanded ? "" : "line-clamp-3"}`}>
            {clauseText}
          </p>
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="mt-2 text-xs font-black uppercase tracking-wide text-[#185FA5]"
          >
            {expanded ? "Show less" : "Show more"}
          </button>
        </div>
      </div>

      <section className="border-t border-slate-200 px-6 py-5">
        <h3 className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Risk Analysis</h3>
        <div className="mt-4 grid gap-3">
          {RISK_AXES.map((axis) => {
            const value = getRiskValue(clause, axis.key);

            return (
              <div key={axis.key} className="grid grid-cols-[92px_minmax(0,1fr)_52px] items-center gap-3">
                <span className="text-xs font-bold uppercase tracking-wide text-slate-600">{axis.label}</span>
                <div className="h-2.5 overflow-hidden rounded-full bg-slate-200">
                  <div className={`h-full rounded-full ${getRiskBarColor(value)}`} style={{ width: `${value * 10}%` }} />
                </div>
                <span className="text-right text-xs font-black text-slate-700">{value.toFixed(1)}/10</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="mx-6 mb-5 rounded-lg border border-l-8 border-[#A32D2D] border-r-red-950 border-t-red-950 border-b-red-950 bg-[#1a0a0a] p-5 shadow-[0_18px_46px_rgba(163,45,45,0.32)]">
        <div className="flex items-center gap-2 text-red-200">
          <GavelIcon />
          <h3 className="text-xs font-black uppercase tracking-[0.22em]">Hostile Lawyer Analysis</h3>
        </div>
        <p className="mt-3 text-sm font-semibold leading-6 text-red-50">
          {clause.adversary_argument || "Adversary argument unavailable."}
        </p>
      </section>

      <section className="mx-6 mb-6 rounded-lg border border-l-8 border-[#3B6D11] border-r-green-950 border-t-green-950 border-b-green-950 bg-[#0a1a0a] p-5">
        <h3 className="text-xs font-black uppercase tracking-[0.18em] text-green-200">
          How To Negotiate This
        </h3>
        <p className="mt-3 text-sm font-semibold leading-6 text-green-50">
          {clause.negotiation_recommendation || "Recommendation unavailable."}
        </p>
      </section>
    </article>
  );
}
