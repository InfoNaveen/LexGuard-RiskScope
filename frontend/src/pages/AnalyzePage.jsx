import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ClauseCard from "../components/ClauseCard.jsx";
import SummaryPanel from "../components/SummaryPanel.jsx";
import { backendWsUrl } from "../lib/api.js";
import { mergeClause } from "../lib/risk.js";

function eventName(message) {
  return message?.event || message?.type || message?.status;
}

function valuesFromStore(store, readyOrder) {
  return readyOrder.map((clauseId) => store[clauseId]).filter((clause) => clause?.ready);
}

export default function AnalyzePage() {
  const { job_id: jobId = "" } = useParams();
  const clauseStoreRef = useRef({});
  const readyOrderRef = useRef([]);
  const socketRef = useRef(null);
  const reconnectsRef = useRef(0);
  const completedRef = useRef(false);
  const failedRef = useRef(false);
  const processedRef = useRef(0);
  const totalRef = useRef(0);

  const [readyClauses, setReadyClauses] = useState([]);
  const [processedClauses, setProcessedClauses] = useState(0);
  const [totalClauses, setTotalClauses] = useState(0);
  const [status, setStatus] = useState("Connecting to analysis service...");
  const [socketError, setSocketError] = useState("");
  const [jobComplete, setJobComplete] = useState(false);
  const [failed, setFailed] = useState(false);
  const [connectionAttempt, setConnectionAttempt] = useState(0);

  const syncReadyClauses = useCallback(() => {
    setReadyClauses(valuesFromStore(clauseStoreRef.current, readyOrderRef.current));
  }, []);

  const mergeClausePatch = useCallback((clauseId, patch, markReady = false) => {
    if (!clauseId) {
      return;
    }

    const nextClause = mergeClause(clauseStoreRef.current[clauseId], {
      clause_id: clauseId,
      ...patch,
      ready: markReady || clauseStoreRef.current[clauseId]?.ready || false,
    });

    clauseStoreRef.current = {
      ...clauseStoreRef.current,
      [clauseId]: nextClause,
    };

    if (markReady && !readyOrderRef.current.includes(clauseId)) {
      readyOrderRef.current = [...readyOrderRef.current, clauseId];
    }

    if (nextClause.ready) {
      syncReadyClauses();
    }
  }, [syncReadyClauses]);

  const connect = useCallback(() => {
    let closedByCleanup = false;
    setSocketError("");
    setStatus("Connecting to analysis service...");

    try {
      const socket = new WebSocket(backendWsUrl(`/ws/${encodeURIComponent(jobId)}`));
      socketRef.current = socket;

      socket.onopen = () => {
        if (!closedByCleanup) {
          setStatus("Analysis stream connected.");
          setSocketError("");
        }
      };

      socket.onmessage = (event) => {
        if (closedByCleanup) {
          return;
        }

        try {
          const message = JSON.parse(event.data);
          const name = eventName(message);

          if (name === "started") {
            setStatus("Analysis started. Waiting for clause events...");
            return;
          }

          if (name === "extractor_complete") {
            mergeClausePatch(message.clause_id, {
              clause_type: message.data?.clause_type,
            });
            setStatus("Clause extracted.");
            return;
          }

          if (name === "analyst_complete") {
            mergeClausePatch(message.clause_id, {
              risk_scores: message.data?.risk_scores || {},
            });
            setStatus("Risk analysis received.");
            return;
          }

          if (name === "adversary_complete") {
            mergeClausePatch(message.clause_id, {
              adversary_argument: message.data?.adversary_argument,
            });
            setStatus("Hostile lawyer analysis received.");
            return;
          }

          if (name === "advisor_complete") {
            mergeClausePatch(message.clause_id, {
              plain_language_summary: message.data?.plain_language_summary,
              severity: message.data?.severity,
              negotiation_recommendation: message.data?.negotiation_recommendation,
            }, true);
            setStatus("Clause ready.");
            return;
          }

          if (name === "clause_complete") {
            processedRef.current += 1;
            setProcessedClauses(processedRef.current);
            setStatus(`Analyzing clause ${processedRef.current} of ${totalRef.current || "?"}`);
            return;
          }

          if (name === "job_complete") {
            const nextTotal = Number(message.data?.total_clauses || readyOrderRef.current.length);
            const nextProcessed = Number(message.data?.processed_clauses || processedRef.current || nextTotal);
            totalRef.current = nextTotal;
            processedRef.current = nextProcessed;
            completedRef.current = true;
            setTotalClauses(nextTotal);
            setProcessedClauses(nextProcessed);
            setJobComplete(true);
            setStatus("Analysis complete.");
            setSocketError("");
            socket.close();
            return;
          }

          if (name === "failed" || message.data?.status === "failed") {
            failedRef.current = true;
            setFailed(true);
            setStatus("Analysis failed.");
            socket.close();
          }
        } catch (error) {
          setSocketError(error.message || "Could not parse WebSocket event.");
        }
      };

      socket.onerror = () => {
        if (!closedByCleanup && !completedRef.current && !failedRef.current) {
          setStatus("Analysis stream interrupted.");
        }
      };

      socket.onclose = () => {
        if (closedByCleanup || completedRef.current || failedRef.current) {
          return;
        }

        if (reconnectsRef.current < 1) {
          reconnectsRef.current += 1;
          setStatus("Connection dropped. Reconnecting...");
          window.setTimeout(() => setConnectionAttempt((attempt) => attempt + 1), 500);
          return;
        }

        setSocketError("Analysis service unavailable. The live stream disconnected.");
        setStatus("Analysis stream disconnected.");
      };
    } catch (error) {
      setSocketError(error.message || "Analysis service unavailable.");
      setStatus("Analysis service unavailable.");
    }

    return () => {
      closedByCleanup = true;
      socketRef.current?.close();
    };
  }, [jobId, mergeClausePatch]);

  useEffect(() => connect(), [connect, connectionAttempt]);

  const progressPercent = useMemo(() => {
    if (!totalClauses) {
      return jobComplete ? 100 : 0;
    }

    return Math.min(100, Math.round((processedClauses / totalClauses) * 100));
  }, [jobComplete, processedClauses, totalClauses]);

  const manualRetry = () => {
    reconnectsRef.current = 0;
    completedRef.current = false;
    failedRef.current = false;
    setSocketError("");
    setConnectionAttempt((attempt) => attempt + 1);
  };

  if (failed) {
    return (
      <main className="min-h-screen bg-white">
        <div className="grid min-h-screen lg:grid-cols-[360px_minmax(0,1fr)]">
          <aside className="bg-[#0f1117] px-8 py-10 text-white">
            <p className="text-xs font-black uppercase tracking-[0.25em] text-slate-400">LexGuard</p>
            <h1 className="mt-3 text-4xl font-black">RiskScope</h1>
          </aside>
          <section className="flex items-center justify-center px-6 py-12">
            <div className="max-w-xl rounded-lg border border-red-200 bg-red-50 p-6">
              <p className="text-xs font-black uppercase tracking-[0.2em] text-[#A32D2D]">Analysis Failed</p>
              <h2 className="mt-2 text-2xl font-black text-red-950">Analysis failed</h2>
              <p className="mt-3 text-sm leading-6 text-red-900">The backend reported a failed job for {jobId}.</p>
              <Link to="/" className="mt-5 inline-flex h-11 items-center justify-center rounded-md bg-[#A32D2D] px-4 text-sm font-black text-white">
                Re-upload Contract
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white">
      <div className="grid min-h-screen lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="bg-[#0f1117] px-7 py-8 text-white">
          <p className="text-xs font-black uppercase tracking-[0.25em] text-slate-400">LexGuard</p>
          <h1 className="mt-3 text-3xl font-black">RiskScope</h1>
          <p className="mt-4 text-sm leading-6 text-slate-300">Live contract intelligence stream.</p>
          <Link to="/" className="mt-8 inline-flex h-10 items-center justify-center rounded-md border border-white/15 px-4 text-sm font-black text-white hover:bg-white/10">
            New Upload
          </Link>
        </aside>

        <section className="px-6 py-8">
          <div className={jobComplete ? "grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]" : ""}>
            <div className="mx-auto w-full max-w-6xl">
              <div className="mb-8 border-b border-slate-200 pb-6">
                <p className="text-xs font-black uppercase tracking-[0.2em] text-[#185FA5]">Live Analysis</p>
                <h2 className="mt-2 text-3xl font-black text-slate-950">Clause Risk Audit</h2>
                <p className="mt-3 text-sm font-semibold text-slate-600">Job ID: {jobId}</p>
              </div>

              <div className="mb-6 rounded-lg border border-slate-200 bg-slate-50 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm font-black text-slate-950">{status}</p>
                  <p className="text-sm font-black text-[#185FA5]">{progressPercent}%</p>
                </div>
                <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full rounded-full bg-[#185FA5] transition-all duration-300" style={{ width: `${progressPercent}%` }} />
                </div>
                <p className="mt-3 text-xs font-bold uppercase tracking-wide text-slate-500">
                  Analyzing clause {processedClauses} of {totalClauses || "?"}
                </p>
              </div>

              {socketError ? (
                <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-red-200 bg-red-50 p-4">
                  <p className="text-sm font-semibold text-[#A32D2D]">{socketError}</p>
                  <button type="button" onClick={manualRetry} className="inline-flex h-10 items-center justify-center rounded-md bg-[#A32D2D] px-4 text-sm font-black text-white">
                    Retry WebSocket
                  </button>
                </div>
              ) : null}

              <div className="space-y-6">
                {readyClauses.length ? (
                  readyClauses.map((clause) => <ClauseCard key={clause.clause_id} clause={clause} />)
                ) : (
                  <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
                    <p className="text-sm font-black text-slate-700">Waiting for advisor_complete events...</p>
                  </div>
                )}
              </div>
            </div>

            {jobComplete ? (
              <div className="mt-8 xl:mt-0">
                <SummaryPanel jobId={jobId} clauses={readyClauses} totalClauses={totalClauses} />
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}
