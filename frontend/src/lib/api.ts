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
};

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
): Promise<AssessResponse> {
  const res = await fetch(`${baseUrl()}/api/assess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: email?.trim() || null,
      answers,
    }),
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const err: { detail?: unknown } = await res.json();
      const d = err.detail;
      if (typeof d === "string") message = d;
      else if (Array.isArray(d) && d[0] && typeof d[0] === "object" && "msg" in d[0]) {
        message = String((d[0] as { msg: string }).msg);
      } else if (d) message = JSON.stringify(d);
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return res.json();
}
