"use client";

import { useCallback, useEffect, useState } from "react";
import type { AdminSubmissionRow, AssessResponse, Question } from "@/lib/api";
import {
  adminDownloadCsv,
  adminFetchSubmissions,
  adminFetchSummary,
  adminLogin,
  fetchQuestions,
} from "@/lib/api";
import { bandTheme } from "@/lib/bandTheme";

const TOKEN_KEY = "beacon_ind_admin_jwt";

function clientRiskSnapshot(
  answers: Record<string, string>,
  report: AssessResponse,
) {
  const q13 = answers["q13"];
  const timeline: Record<string, [string, number | null]> = {
    "0_6": ["0–6 months to IND target", 90],
    "6_12": ["6–12 months to IND target", 270],
    "12_18": ["12–18 months to IND target", 450],
    "18_plus": ["18+ months to IND target", null],
  };
  const [deadline, days] = timeline[q13] ?? ["Timeline not specified", null];
  const gaps = report.critical_gaps.length;
  const est = Math.min(120, Math.max(8, 8 + gaps * 14));
  return { deadline, days, est, gaps };
}

function labelAnswer(questions: Question[], qid: string, aid: string): string {
  const q = questions.find((x) => x.id === qid);
  return q?.options.find((o) => o.id === aid)?.label ?? aid;
}

export default function AdminPanel() {
  const [open, setOpen] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<Awaited<
    ReturnType<typeof adminFetchSummary>
  > | null>(null);
  const [page, setPage] = useState(1);
  const [subs, setSubs] = useState<{
    total: number;
    items: AdminSubmissionRow[];
  } | null>(null);
  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [selected, setSelected] = useState<AdminSubmissionRow | null>(null);

  useEffect(() => {
    const t = sessionStorage.getItem(TOKEN_KEY);
    if (t) setToken(t);
  }, []);

  const loadDashboard = useCallback(async (t: string) => {
    setLoading(true);
    try {
      const [sum, subPage, qs] = await Promise.all([
        adminFetchSummary(t),
        adminFetchSubmissions(t, 1, 50),
        fetchQuestions(),
      ]);
      setSummary(sum);
      setSubs({ total: subPage.total, items: subPage.items });
      setPage(1);
      setQuestions(qs);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open && token) {
      loadDashboard(token);
    }
  }, [open, token, loadDashboard]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoading(true);
    try {
      const t = await adminLogin(email.trim(), password);
      sessionStorage.setItem(TOKEN_KEY, t);
      setToken(t);
      setPassword("");
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setSummary(null);
    setSubs(null);
    setSelected(null);
  };

  const refreshPage = async (p: number) => {
    if (!token) return;
    setLoading(true);
    try {
      const subPage = await adminFetchSubmissions(token, p, 50);
      setSubs({ total: subPage.total, items: subPage.items });
      setPage(p);
    } finally {
      setLoading(false);
    }
  };

  const downloadCsv = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const blob = await adminDownloadCsv(token);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ind_submissions_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Download failed.");
    } finally {
      setLoading(false);
    }
  };

  const snap =
    selected && questions
      ? clientRiskSnapshot(selected.answers, selected.report)
      : null;
  const bt = selected ? bandTheme(selected.report.band) : null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 rounded-full border border-slate-200 bg-white/95 px-4 py-2 text-xs font-semibold text-slate-600 shadow-lg backdrop-blur-sm hover:bg-slate-50"
      >
        Admin
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
          role="dialog"
          aria-modal="true"
          aria-label="Admin"
        >
          <div className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
              <h2 className="text-sm font-semibold text-slate-900">
                IND Readiness — Admin
              </h2>
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  setSelected(null);
                }}
                className="rounded-lg px-2 py-1 text-sm text-slate-500 hover:bg-slate-100"
              >
                Close
              </button>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto p-5">
              {!token ? (
                <form onSubmit={handleLogin} className="mx-auto max-w-sm space-y-4">
                  <p className="text-sm text-slate-600">
                    Sign in with admin credentials. If login is not configured on
                    the server, you will see a clear error.
                  </p>
                  <label className="block text-sm font-medium text-slate-800">
                    Email
                    <input
                      type="email"
                      autoComplete="username"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                  <label className="block text-sm font-medium text-slate-800">
                    Password
                    <input
                      type="password"
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    />
                  </label>
                  {loginError && (
                    <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">
                      {loginError}
                    </p>
                  )}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full rounded-lg bg-slate-900 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
                  >
                    {loading ? "Signing in…" : "Sign in"}
                  </button>
                </form>
              ) : (
                <div className="space-y-6">
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      onClick={logout}
                      className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700"
                    >
                      Log out
                    </button>
                    <button
                      type="button"
                      onClick={downloadCsv}
                      disabled={loading}
                      className="rounded-lg bg-[var(--beacon-accent,#1d4ed8)] px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
                    >
                      Download CSV
                    </button>
                    <button
                      type="button"
                      onClick={() => token && loadDashboard(token)}
                      disabled={loading}
                      className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600"
                    >
                      Refresh
                    </button>
                  </div>

                  {summary && (
                    <div className="grid gap-3 sm:grid-cols-4">
                      <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div className="text-xs font-medium uppercase text-slate-500">
                          Total
                        </div>
                        <div className="text-2xl font-semibold text-slate-900">
                          {summary.total}
                        </div>
                      </div>
                      <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div className="text-xs font-medium uppercase text-slate-500">
                          With email
                        </div>
                        <div className="text-2xl font-semibold text-slate-900">
                          {summary.with_email}
                        </div>
                      </div>
                      <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div className="text-xs font-medium uppercase text-slate-500">
                          No email
                        </div>
                        <div className="text-2xl font-semibold text-slate-900">
                          {summary.without_email}
                        </div>
                      </div>
                      <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                        <div className="text-xs font-medium uppercase text-slate-500">
                          By band
                        </div>
                        <div className="text-xs text-slate-700">
                          {Object.entries(summary.by_band)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(" · ")}
                        </div>
                      </div>
                    </div>
                  )}

                  {subs && (
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="min-w-full text-left text-sm">
                        <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                          <tr>
                            <th className="px-3 py-2">When</th>
                            <th className="px-3 py-2">Email</th>
                            <th className="px-3 py-2">Band</th>
                            <th className="px-3 py-2">Score</th>
                            <th className="px-3 py-2">Consent</th>
                          </tr>
                        </thead>
                        <tbody>
                          {subs.items.map((row) => (
                            <tr
                              key={row.id}
                              className="cursor-pointer border-t border-slate-100 hover:bg-slate-50/80"
                              onClick={() => setSelected(row)}
                            >
                              <td className="px-3 py-2 text-slate-600">
                                {row.created_at
                                  ? new Date(row.created_at).toLocaleString()
                                  : "—"}
                              </td>
                              <td className="px-3 py-2">{row.email ?? "—"}</td>
                              <td className="px-3 py-2">
                                {row.report?.band ?? "—"}
                              </td>
                              <td className="px-3 py-2">
                                {row.report?.percentage != null
                                  ? `${row.report.percentage}%`
                                  : "—"}
                              </td>
                              <td className="px-3 py-2">
                                {row.consent ? "Yes" : "No"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {subs && subs.total > 50 && (
                    <div className="flex gap-2 text-sm">
                      <button
                        type="button"
                        disabled={page <= 1 || loading}
                        onClick={() => refreshPage(page - 1)}
                        className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
                      >
                        Previous
                      </button>
                      <span className="py-1 text-slate-600">
                        Page {page} · {subs.total} total
                      </span>
                      <button
                        type="button"
                        disabled={page * 50 >= subs.total || loading}
                        onClick={() => refreshPage(page + 1)}
                        className="rounded border border-slate-200 px-3 py-1 disabled:opacity-40"
                      >
                        Next
                      </button>
                    </div>
                  )}

                  {selected && questions && bt && snap && (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-5">
                      <div className="mb-4 flex items-start justify-between gap-3">
                        <h3 className="text-sm font-semibold text-slate-900">
                          Submission {selected.id}
                        </h3>
                        <button
                          type="button"
                          onClick={() => setSelected(null)}
                          className="text-xs text-slate-500 hover:underline"
                        >
                          Clear
                        </button>
                      </div>

                      <div
                        className={`rounded-2xl border bg-white p-6 shadow-sm ring-1 ${bt.ring}`}
                      >
                        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                              Your IND readiness
                            </p>
                            <p className="mt-1 text-3xl font-semibold tabular-nums text-slate-900">
                              {selected.report.percentage}%
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              Model: {selected.report.weighted_points} /{" "}
                              {selected.report.max_points} weighted
                            </p>
                          </div>
                          <span
                            className={`inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-semibold ${bt.badge}`}
                          >
                            {selected.report.band_title}
                          </span>
                        </div>
                        <p
                          className={`mt-4 text-sm leading-relaxed ${bt.text}`}
                        >
                          {selected.report.band_description}
                        </p>
                        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full ${bt.bar}`}
                            style={{
                              width: `${Math.min(100, selected.report.percentage)}%`,
                            }}
                          />
                        </div>
                      </div>

                      <div className="mt-4 grid gap-4 sm:grid-cols-2">
                        <div>
                          <h4 className="text-xs font-bold uppercase text-slate-500">
                            Critical gaps
                          </h4>
                          <ul className="mt-2 space-y-2 text-sm text-slate-800">
                            {selected.report.critical_gaps.length === 0 ? (
                              <li className="text-slate-500">None flagged.</li>
                            ) : (
                              selected.report.critical_gaps.map((g) => (
                                <li key={g.message}>
                                  <span className="font-medium">{g.message}</span>
                                  <span className="mt-0.5 block text-xs text-slate-600">
                                    {g.risk_note}
                                  </span>
                                </li>
                              ))
                            )}
                          </ul>
                        </div>
                        <div>
                          <h4 className="text-xs font-bold uppercase text-slate-500">
                            Risk snapshot
                          </h4>
                          <dl className="mt-2 space-y-2 text-sm">
                            <div>
                              <dt className="text-slate-500">Deadline / window</dt>
                              <dd className="font-medium text-slate-900">
                                {snap.deadline}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-slate-500">Days (heuristic)</dt>
                              <dd className="font-medium text-slate-900">
                                {snap.days != null
                                  ? `~${snap.days} days`
                                  : "N/A"}
                              </dd>
                            </div>
                            <div>
                              <dt className="text-slate-500">Est. remediation</dt>
                              <dd className="font-medium text-slate-900">
                                ~{snap.est} hours (ROM)
                              </dd>
                            </div>
                          </dl>
                        </div>
                      </div>

                      <div className="mt-4">
                        <h4 className="text-xs font-bold uppercase text-slate-500">
                          Responses
                        </h4>
                        <div className="mt-2 overflow-x-auto rounded-lg border border-slate-200 bg-white">
                          <table className="min-w-full text-left text-sm">
                            <thead className="bg-slate-50 text-xs text-slate-500">
                              <tr>
                                <th className="px-2 py-2">#</th>
                                <th className="px-2 py-2">Section</th>
                                <th className="px-2 py-2">Question</th>
                                <th className="px-2 py-2">Answer</th>
                              </tr>
                            </thead>
                            <tbody>
                              {questions.map((q) => (
                                <tr
                                  key={q.id}
                                  className="border-t border-slate-100"
                                >
                                  <td className="px-2 py-2 text-slate-400">
                                    {q.order}
                                  </td>
                                  <td className="px-2 py-2 text-slate-600">
                                    {q.section}
                                  </td>
                                  <td className="px-2 py-2 text-slate-800">
                                    {q.text}
                                  </td>
                                  <td className="px-2 py-2 font-medium text-[var(--beacon-accent,#1d4ed8)]">
                                    {labelAnswer(
                                      questions,
                                      q.id,
                                      selected.answers[q.id] ?? "",
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {selected.meta && Object.keys(selected.meta).length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-xs font-bold uppercase text-slate-500">
                            Meta
                          </h4>
                          <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-100">
                            {JSON.stringify(selected.meta, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
