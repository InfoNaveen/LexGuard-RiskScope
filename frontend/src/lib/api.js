const rawPipelineUrl = import.meta.env.VITE_PIPELINE_URL || "";
const rawBackendUrl = import.meta.env.VITE_BACKEND_URL || "";

function normalizeHttpUrl(value) {
  const trimmed = value.replace(/\/$/, "");

  if (!trimmed) {
    return "";
  }

  return /^https?:\/\//.test(trimmed) ? trimmed : `https://${trimmed}`;
}

export const PIPELINE_BASE_URL = normalizeHttpUrl(rawPipelineUrl);
export const BACKEND_BASE_URL = normalizeHttpUrl(rawBackendUrl);

function requireUrl(value, label) {
  if (!value) {
    throw new Error(`${label} is not configured.`);
  }
}

function backendApiUrl(path) {
  requireUrl(BACKEND_BASE_URL, "VITE_BACKEND_URL");
  return import.meta.env.DEV ? path : `${BACKEND_BASE_URL}${path}`;
}

export function backendWsUrl(path) {
  requireUrl(BACKEND_BASE_URL, "VITE_BACKEND_URL");

  if (import.meta.env.DEV) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${path}`;
  }

  return `${BACKEND_BASE_URL.replace(/^http:/, "ws:").replace(/^https:/, "wss:")}${path}`;
}

export async function uploadContract(file) {
  requireUrl(PIPELINE_BASE_URL, "VITE_PIPELINE_URL");
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${PIPELINE_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}.`);
  }

  return response.json();
}

export async function startAnalysis(jobId) {
  const response = await fetch(backendApiUrl(`/api/analyze/${encodeURIComponent(jobId)}`));

  if (!response.ok) {
    throw new Error(`Analysis failed to start with status ${response.status}.`);
  }

  return response.json();
}

export async function fetchReport(jobId) {
  const response = await fetch(backendApiUrl(`/api/report/${encodeURIComponent(jobId)}`));

  if (!response.ok) {
    throw new Error(`Report download failed with status ${response.status}.`);
  }

  return response.json();
}

export async function downloadReport(jobId) {
  const report = await fetchReport(jobId);
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = objectUrl;
  anchor.download = `lexguard-report-${jobId}.json`;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
