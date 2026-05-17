export const RISK_AXES = [
  { key: "financial_risk", label: "Financial" },
  { key: "privacy_risk", label: "Privacy" },
  { key: "ip_risk", label: "IP" },
  { key: "employment_risk", label: "Employment" },
  { key: "compliance_risk", label: "Compliance" },
];

export const severityStyles = {
  critical: "border-[#A32D2D] bg-[#A32D2D] text-white",
  high: "border-[#BA7517] bg-[#BA7517] text-white",
  medium: "border-[#854F0B] bg-[#854F0B] text-white",
  low: "border-[#3B6D11] bg-[#3B6D11] text-white",
};

export const severityDots = {
  critical: "bg-[#A32D2D]",
  high: "bg-[#BA7517]",
  medium: "bg-[#854F0B]",
  low: "bg-[#3B6D11]",
};

export const clauseTypeStyles = {
  "non-compete": "border-red-200 bg-red-50 text-red-900",
  "IP-transfer": "border-purple-200 bg-purple-50 text-purple-900",
  arbitration: "border-blue-200 bg-blue-50 text-blue-900",
  termination: "border-slate-300 bg-slate-100 text-slate-900",
  "data-collection": "border-cyan-200 bg-cyan-50 text-cyan-900",
  liability: "border-orange-200 bg-orange-50 text-orange-900",
  "auto-renewal": "border-amber-200 bg-amber-50 text-amber-900",
  other: "border-slate-200 bg-slate-50 text-slate-700",
};

export function normalizeSeverity(severity) {
  const normalized = String(severity || "low").toLowerCase();
  return ["critical", "high", "medium", "low"].includes(normalized) ? normalized : "low";
}

export function getClauseType(clause) {
  return clause?.clause_type || "other";
}

export function getClauseText(clause) {
  return (
    clause?.clause_text ||
    clause?.text ||
    clause?.source_text ||
    clause?.plain_language_summary ||
    "Original clause text was not included in the live event stream."
  );
}

export function getRiskValue(clause, key) {
  const value = Number(clause?.risk_scores?.[key] ?? 0);
  return Number.isFinite(value) ? Math.max(0, Math.min(10, value)) : 0;
}

export function getRiskBarColor(value) {
  if (value >= 8) {
    return "bg-[#A32D2D]";
  }

  if (value >= 5) {
    return "bg-[#BA7517]";
  }

  return "bg-[#3B6D11]";
}

export function getMaxRiskScore(clause) {
  return Math.max(...RISK_AXES.map((axis) => getRiskValue(clause, axis.key)));
}

export function mergeClause(existingClause, patch) {
  return {
    ...(existingClause || {}),
    ...patch,
    risk_scores: {
      ...(existingClause?.risk_scores || {}),
      ...(patch?.risk_scores || {}),
    },
  };
}
