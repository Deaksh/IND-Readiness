"use client";

import { useCallback, useMemo, useState } from "react";
import type { AssessResponse, Question } from "@/lib/api";
import { fetchQuestions, submitAssessment } from "@/lib/api";
import { bandTheme } from "@/lib/bandTheme";

type Phase = "intro" | "questions" | "email" | "results";

const BEACON_WEBSITE = "https://beacon-bio.carrd.co";
const EARLY_ACCESS_WAITLIST_URL =
  "https://docs.google.com/forms/d/e/1FAIpQLSeKtKgRz6EKmOEewGL5NIbCmDiHrM0T47xekYDzx_1ouLWg7w/viewform";

const SECTION_ORDER = ["Analytical Data", "CMC Documentation", "Regulatory Strategy"] as const;

function groupBySection(questions: Question[]) {
  const map = new Map<string, Question[]>();
  for (const q of questions) {
    const list = map.get(q.section) ?? [];
    list.push(q);
    map.set(q.section, list);
  }
  return SECTION_ORDER.map((name) => ({
    name,
    questions: map.get(name) ?? [],
  })).filter((s) => s.questions.length > 0);
}

function collectSubmissionMeta(): Record<string, string | undefined> {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  return {
    page_url: window.location.href,
    referrer: document.referrer || undefined,
    utm_source: params.get("utm_source") || undefined,
    utm_medium: params.get("utm_medium") || undefined,
    utm_campaign: params.get("utm_campaign") || undefined,
  };
}

export default function BeaconAssessment() {
  const [phase, setPhase] = useState<Phase>("intro");
  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [sectionIdx, setSectionIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [email, setEmail] = useState("");
  const [emailConsent, setEmailConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<AssessResponse | null>(null);

  const sections = useMemo(
    () => (questions ? groupBySection(questions) : []),
    [questions],
  );

  const totalQs = questions?.length ?? 0;
  const answeredCount = useMemo(
    () => Object.keys(answers).length,
    [answers],
  );

  const start = useCallback(async () => {
    setLoadError(null);
    try {
      const qs = await fetchQuestions();
      setQuestions(qs);
      setSectionIdx(0);
      setAnswers({});
      setPhase("questions");
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Failed to load.");
    }
  }, []);

  const currentSection = sections[sectionIdx];
  const sectionComplete =
    currentSection?.questions.every((q) => answers[q.id]) ?? false;

  const allAnswered =
    totalQs > 0 &&
    questions!.every((q) => Boolean(answers[q.id]));

  const goNextSection = () => {
    if (sectionIdx < sections.length - 1) setSectionIdx((i) => i + 1);
    else setPhase("email");
  };

  const goPrevSection = () => {
    if (sectionIdx > 0) setSectionIdx((i) => i - 1);
    else setPhase("intro");
  };

  const runAssessment = async () => {
    if (!questions) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await submitAssessment(email.trim() || undefined, answers, {
        consent: emailConsent,
        meta: collectSubmissionMeta(),
      });
      setResult(res);
      setPhase("results");
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : "Could not submit.");
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setPhase("intro");
    setQuestions(null);
    setSectionIdx(0);
    setAnswers({});
    setEmail("");
    setEmailConsent(false);
    setResult(null);
    setSubmitError(null);
    setLoadError(null);
  };

  return (
    <div className="relative mx-auto max-w-3xl px-4 pb-24 pt-12 sm:px-6 lg:px-8">
      <header className="mb-10 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--beacon-muted)]">
          Beacon
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[var(--beacon-ink)] sm:text-4xl">
          IND Readiness Assessment
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-[var(--beacon-muted)]">
          A concise, IND-focused questionnaire covering analytical data, CMC
          documentation, and regulatory strategy. Estimated time: about two
          minutes.
        </p>
        <p className="mt-4 text-sm">
          <a
            href={BEACON_WEBSITE}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-[var(--beacon-accent)] underline decoration-[var(--beacon-accent)]/30 underline-offset-4 transition hover:decoration-[var(--beacon-accent)]"
          >
            {BEACON_WEBSITE.replace(/^https?:\/\//, "")}
          </a>
        </p>
      </header>

      {phase === "intro" && (
        <div className="rounded-2xl border border-[var(--beacon-border)] bg-white/80 p-8 shadow-[var(--beacon-shadow)] backdrop-blur-sm">
          <ul className="space-y-3 text-sm text-[var(--beacon-ink)]">
            <li className="flex gap-3">
              <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--beacon-accent-soft)] text-xs font-bold text-[var(--beacon-accent)]">
                1
              </span>
              <span>
                <strong className="font-medium">Analytical data</strong> —
                methods, data integrity, and audit readiness.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--beacon-accent-soft)] text-xs font-bold text-[var(--beacon-accent)]">
                2
              </span>
              <span>
                <strong className="font-medium">CMC documentation</strong> —
                M4Q narratives, version control, and eCTD alignment.
              </span>
            </li>
            <li className="flex gap-3">
              <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--beacon-accent-soft)] text-xs font-bold text-[var(--beacon-accent)]">
                3
              </span>
              <span>
                <strong className="font-medium">Regulatory strategy</strong> —
                mapping, resourcing, timelines, and risk mitigation.
              </span>
            </li>
          </ul>
          {loadError && (
            <p className="mt-6 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">
              {loadError}
            </p>
          )}
          <button
            type="button"
            onClick={start}
            className="mt-8 w-full rounded-xl bg-[var(--beacon-accent)] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--beacon-accent)]"
          >
            Start assessment
          </button>
        </div>
      )}

      {phase === "questions" && questions && currentSection && (
        <div className="space-y-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-[var(--beacon-muted)]">
                Section {sectionIdx + 1} of {sections.length}
              </p>
              <p className="text-lg font-semibold text-[var(--beacon-ink)]">
                {currentSection.name}
              </p>
            </div>
            <div className="text-right text-sm text-[var(--beacon-muted)]">
              {answeredCount} / {totalQs} answered
            </div>
          </div>

          <div className="h-2 overflow-hidden rounded-full bg-slate-200/80">
            <div
              className="h-full rounded-full bg-[var(--beacon-accent)] transition-all duration-300"
              style={{
                width: `${totalQs ? (answeredCount / totalQs) * 100 : 0}%`,
              }}
            />
          </div>

          <div className="space-y-8">
            {currentSection.questions.map((q) => (
              <fieldset
                key={q.id}
                className="rounded-2xl border border-[var(--beacon-border)] bg-white/90 p-6 shadow-sm"
              >
                <legend className="sr-only">{q.text}</legend>
                <p className="text-sm font-medium text-[var(--beacon-ink)]">
                  <span className="mr-2 text-[var(--beacon-muted)]">
                    Q{q.order}.
                  </span>
                  {q.text}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {q.options.map((opt) => {
                    const selected = answers[q.id] === opt.id;
                    return (
                      <label
                        key={opt.id}
                        className={`cursor-pointer rounded-full border px-4 py-2 text-sm transition ${
                          selected
                            ? "border-[var(--beacon-accent)] bg-[var(--beacon-accent-soft)] font-medium text-[var(--beacon-accent)]"
                            : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                        }`}
                      >
                        <input
                          type="radio"
                          className="sr-only"
                          name={q.id}
                          value={opt.id}
                          checked={selected}
                          onChange={() =>
                            setAnswers((a) => ({ ...a, [q.id]: opt.id }))
                          }
                        />
                        {opt.label}
                      </label>
                    );
                  })}
                </div>
              </fieldset>
            ))}
          </div>

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
            <button
              type="button"
              onClick={goPrevSection}
              className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
            >
              Back
            </button>
            <button
              type="button"
              disabled={!sectionComplete}
              onClick={goNextSection}
              className="rounded-xl bg-[var(--beacon-accent)] px-5 py-3 text-sm font-semibold text-white shadow-sm transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {sectionIdx < sections.length - 1 ? "Next section" : "Continue"}
            </button>
          </div>

          {sectionIdx === sections.length - 1 && !allAnswered && (
            <p className="text-center text-xs text-amber-800">
              Answer all questions in each section to continue.
            </p>
          )}
        </div>
      )}

      {phase === "email" && (
        <div className="rounded-2xl border border-[var(--beacon-border)] bg-white/90 p-8 shadow-[var(--beacon-shadow)]">
          <h2 className="text-xl font-semibold text-[var(--beacon-ink)]">
            Your personalized report
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-[var(--beacon-muted)]">
            Enter your work email to receive your IND readiness score, critical
            gaps, and recommended next steps. We&apos;ll only use this to follow
            up if you request help with remediation.
          </p>
          <label className="mt-6 block text-sm font-medium text-[var(--beacon-ink)]">
            Work email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-inner outline-none ring-0 transition focus:border-[var(--beacon-accent)] focus:ring-2 focus:ring-[var(--beacon-accent)]/20"
            />
          </label>
          <label className="mt-4 flex cursor-pointer items-start gap-3 text-sm text-[var(--beacon-ink)]">
            <input
              type="checkbox"
              checked={emailConsent}
              onChange={(e) => setEmailConsent(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-slate-300"
            />
            <span>
              I agree to receive my personalized IND readiness report and a copy
              of these results by email. You can unsubscribe from follow-ups at
              any time.
            </span>
          </label>
          {submitError && (
            <p className="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">
              {submitError}
            </p>
          )}
          <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
            <button
              type="button"
              onClick={() => setPhase("questions")}
              className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-medium text-slate-700"
            >
              Back to questions
            </button>
            <button
              type="button"
              disabled={submitting || !email.trim() || !emailConsent}
              onClick={runAssessment}
              className="rounded-xl bg-[var(--beacon-accent)] px-5 py-3 text-sm font-semibold text-white shadow-sm transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {submitting ? "Scoring…" : "View my report"}
            </button>
          </div>
          <p className="mt-4 text-center text-xs text-slate-500">
            Or{" "}
            <button
              type="button"
              className="font-medium text-[var(--beacon-accent)] underline-offset-2 hover:underline"
              onClick={async () => {
                setSubmitting(true);
                setSubmitError(null);
                try {
                  const res = await submitAssessment(undefined, answers, {
                    consent: false,
                    meta: collectSubmissionMeta(),
                  });
                  setResult(res);
                  setPhase("results");
                } catch (e) {
                  setSubmitError(
                    e instanceof Error ? e.message : "Could not submit.",
                  );
                } finally {
                  setSubmitting(false);
                }
              }}
            >
              skip email and show results only
            </button>
          </p>
        </div>
      )}

      {phase === "results" && result && (
        <div className="space-y-8">
          <div
            className={`rounded-2xl border bg-white/95 p-8 shadow-[var(--beacon-shadow)] ring-1 ${bandTheme(result.band).ring}`}
          >
            <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--beacon-muted)]">
                  Your IND readiness
                </p>
                <p className="mt-2 text-4xl font-semibold tabular-nums text-[var(--beacon-ink)]">
                  {result.percentage}%
                </p>
                <p className="mt-1 text-sm text-[var(--beacon-muted)]">
                  Weighted score across {Math.round(result.max_points)}{" "}
                  dimensions
                </p>
              </div>
              <span
                className={`inline-flex w-fit items-center rounded-full px-4 py-1.5 text-xs font-semibold ${bandTheme(result.band).badge}`}
              >
                {result.band_title}
              </span>
            </div>
            <p className={`mt-6 text-sm leading-relaxed ${bandTheme(result.band).text}`}>
              {result.band_description}
            </p>
            <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full transition-all ${bandTheme(result.band).bar}`}
                style={{ width: `${Math.min(100, result.percentage)}%` }}
              />
            </div>
          </div>

          <section className="rounded-2xl border border-[var(--beacon-border)] bg-white/95 p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-[var(--beacon-ink)]">
              Critical gaps
            </h2>
            {result.critical_gaps.length === 0 ? (
              <p className="mt-3 text-sm text-[var(--beacon-muted)]">
                No automated red-flag gaps from your answers. Still validate
                against your quality system and recent FDA guidance.
              </p>
            ) : (
              <ul className="mt-4 space-y-3">
                {result.critical_gaps.map((g) => (
                  <li
                    key={g.message}
                    className="flex gap-3 rounded-xl border border-rose-100 bg-rose-50/80 px-4 py-3 text-sm text-rose-950"
                  >
                    <span className="mt-0.5 text-rose-600" aria-hidden>
                      ✕
                    </span>
                    <span>
                      <span className="font-medium">{g.message}</span>
                      <span className="mt-0.5 block text-xs text-rose-800/90">
                        {g.risk_note}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-2xl border border-[var(--beacon-border)] bg-white/95 p-8 shadow-sm">
            <h2 className="text-lg font-semibold text-[var(--beacon-ink)]">
              Recommended next steps
            </h2>
            <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-[var(--beacon-ink)]">
              {result.recommended_steps.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ol>
          </section>

          <section className="rounded-2xl border border-dashed border-[var(--beacon-border)] bg-[var(--beacon-canvas)]/60 p-8">
            <h2 className="text-lg font-semibold text-[var(--beacon-ink)]">
              Want help closing these gaps?
            </h2>
            <p className="mt-2 text-sm text-[var(--beacon-muted)]">
              Book a free 30-minute IND readiness consultation, or join the Beacon
              early access waitlist.
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <a
                href={result.calendly_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex flex-1 items-center justify-center rounded-xl bg-[var(--beacon-accent)] px-5 py-3 text-center text-sm font-semibold text-white shadow-sm transition hover:brightness-110"
              >
                Book consultation (Calendly)
              </a>
              <a
                href={EARLY_ACCESS_WAITLIST_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex flex-1 items-center justify-center rounded-xl border border-slate-200 bg-white px-5 py-3 text-center text-sm font-semibold text-[var(--beacon-ink)] shadow-sm transition hover:bg-slate-50"
              >
                Join the waitlist (early access)
              </a>
            </div>
          </section>

          <div className="text-center">
            <button
              type="button"
              onClick={reset}
              className="text-sm font-medium text-[var(--beacon-accent)] underline-offset-4 hover:underline"
            >
              Start over
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
