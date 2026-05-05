export type QuestionOption = { id: string; label: string };

export type Question = {
  id: string;
  section: string;
  order: number;
  text: string;
  options: QuestionOption[];
};

export type CriticalGap = {
  message: string;
  risk_note: string;
};

export type AssessResponse = {
  percentage: number;
  band: "green" | "yellow" | "orange" | "red";
  band_title: string;
  band_description: string;
  weighted_points: number;
  max_points: number;
  critical_gaps: CriticalGap[];
  recommended_steps: string[];
  calendly_url: string;
  submission_id?: string | null;
};

export type SubmitOpts = {
  consent?: boolean;
  meta?: Record<string, string | undefined>;
};

async function parseErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const err: { detail?: unknown } = await res.json();
    const d = err.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d) && d[0] && typeof d[0] === "object" && "msg" in d[0]) {
      return String((d[0] as { msg: string }).msg);
    }
    if (d) return JSON.stringify(d);
  } catch {
    /* ignore */
  }
  return fallback;
}

/** Default matches common local uvicorn port; override with NEXT_PUBLIC_API_URL. */
function baseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
    "http://127.0.0.1:8050"
  );
}

export async function fetchQuestions(): Promise<Question[]> {
  const url = `${baseUrl()}/api/questions`;
  let res: Response;
  try {
    res = await fetch(url, { cache: "no-store" });
  } catch (e) {
    const hint =
      typeof window !== "undefined"
        ? ` Is the API running on ${baseUrl()}? (Set NEXT_PUBLIC_API_URL if it uses another host/port.)`
        : "";
    throw new Error(
      `Could not reach the assessment API at ${url}.${hint}${e instanceof Error ? ` (${e.message})` : ""}`,
    );
  }
  if (!res.ok) {
    throw new Error(
      `Could not load assessment questions (${res.status}). Check API at ${baseUrl()}.`,
    );
  }
  return res.json();
}

export async function submitAssessment(
  email: string | undefined,
  answers: Record<string, string>,
  opts?: SubmitOpts,
): Promise<AssessResponse> {
  const rawMeta = opts?.meta;
  const meta =
    rawMeta &&
    Object.fromEntries(
      Object.entries(rawMeta).filter(([, v]) => v != null && String(v).trim() !== ""),
    );
  const res = await fetch(`${baseUrl()}/api/assess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email?.trim() || null,
      answers,
      consent: opts?.consent ?? false,
      meta: meta && Object.keys(meta).length > 0 ? meta : undefined,
    }),
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, res.statusText));
  }
  return res.json();
}

export type AdminSummary = {
  total: number;
  with_email: number;
  without_email: number;
  by_band: Record<string, number>;
  recent: Array<{
    id: string;
    created_at: string | null;
    email: string | null;
    consent: boolean;
    band: string | null;
    percentage: number | null;
  }>;
};

export type AdminSubmissionRow = {
  id: string;
  created_at: string | null;
  email: string | null;
  consent: boolean;
  answers: Record<string, string>;
  report: AssessResponse;
  meta: Record<string, unknown> | null;
};

export async function adminLogin(email: string, password: string): Promise<string> {
  const res = await fetch(`${baseUrl()}/api/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, res.statusText));
  }
  const data: { access_token: string } = await res.json();
  return data.access_token;
}

export async function adminFetchSummary(token: string): Promise<AdminSummary> {
  const res = await fetch(`${baseUrl()}/api/admin/summary`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, res.statusText));
  }
  return res.json();
}

export async function adminFetchSubmissions(
  token: string,
  page: number,
  pageSize: number,
): Promise<{
  page: number;
  page_size: number;
  total: number;
  items: AdminSubmissionRow[];
}> {
  const q = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  const res = await fetch(`${baseUrl()}/api/admin/submissions?${q}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, res.statusText));
  }
  return res.json();
}

export async function adminDownloadCsv(token: string): Promise<Blob> {
  const res = await fetch(`${baseUrl()}/api/admin/submissions/export`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res, res.statusText));
  }
  return res.blob();
}
