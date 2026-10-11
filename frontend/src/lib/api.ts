import { specializations } from "./taxonomy";
export type User = {
  id: string;
  email: string;
  role: "candidate" | "employer";
  verified: boolean;
};
export type Achievement = {
  id: string;
  title: string;
  discipline: string;
  date: string;
  place: number;
  participants: number;
  source: string;
};
export type Match = {
  score: number;
  mode: string;
  baseline_score: number;
  learned_score: number | null;
  blend: { baseline: number; learned: number };
  matched_skills: string[];
  missing_skills: string[];
  explanation: string[];
  factors: { key: string; value: number; contribution: number }[];
  notice: string;
};
export type Profile = {
  id: string;
  name: string;
  city: string;
  bio: string;
  contact?: string;
  email?: string;
  specialization: string;
  desired_grade: string;
  grade: string | null;
  skills: string[];
  experience: number;
  work_format: string;
  salary_min: number;
  score: number;
  verified_at: number | null;
  active_at: number;
  published: boolean;
  consent: boolean;
  fsp_id: string | null;
  achievements: Achievement[];
  contacts_unlocked: boolean;
  grade_change_available_at: number | null;
  match?: Match;
};
export type Need = {
  id: string;
  title: string;
  description: string;
  specialization: string;
  grade: string;
  skills: string[];
  salary_min: number;
  salary_max: number;
  work_format: string;
  company_id: string;
  company_name?: string;
  archived?: boolean;
};
export type Invitation = {
  id: string;
  candidate_id: string;
  company_name: string;
  candidate_name: string;
  title: string;
  message: string;
  salary_min: number;
  salary_max: number;
  contact: string;
  status: string;
  created_at: number;
  contacts_unlocked?: boolean;
  candidate_email?: string;
  candidate_contact?: string;
};
export type Attempt = {
  id: string;
  specialization: string;
  grade: string;
  expires_at: number;
  submitted_at: number | null;
  passed: boolean;
  score: number | null;
  answers: Record<string, string>;
  questions: { id: string; text: string; skill: string; difficulty: number }[];
  outcomes?: { id: string; skill: string; correct: boolean }[];
};
export type Application = {
  created_at: number;
  id: string;
  vacancy_title: string;
  company_name: string;
  candidate_name: string;
  status: string;
  letter: string;
  candidate?: Profile;
};
export type Company = {
  name: string;
  description: string;
  industry: string;
  contact: string;
  city: string;
};
export type Submission = {
  id: string;
  answer: string;
  score: number | null;
  feedback: string;
};
export type Challenge = {
  id: string;
  title: string;
  description: string;
  rubric: string;
  specialization: string;
  company_name: string;
  submissions: Submission[];
};

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...init.headers,
      },
    });
  } catch {
    throw new Error(
      "Нет связи с сервером. Проверьте подключение и повторите действие.",
    );
  }
  const data = await response
    .json()
    .catch(() => ({ detail: "Сервис временно недоступен" }));
  if (
    response.status === 401 &&
    typeof window !== "undefined" &&
    window.location.pathname.startsWith("/app")
  )
    window.dispatchEvent(new Event("session-expired"));
  if (!response.ok)
    throw new ApiError(
      typeof data.detail === "string"
        ? data.detail
        : "Не удалось выполнить запрос",
      response.status,
    );
  return data as T;
}
export const post = <T>(path: string, data: unknown = {}) =>
  api<T>(path, { method: "POST", body: JSON.stringify(data) });
export const put = <T>(path: string, data: unknown) =>
  api<T>(path, { method: "PUT", body: JSON.stringify(data) });
export const patch = <T>(path: string, data: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(data) });
export const specName = (v: string) =>
  specializations.find((s) => s.id === v)?.name || v;
export const gradeName = (v: string | null) =>
  ({ junior: "Начальный", middle: "Средний", senior: "Старший" })[v || ""] ||
  "Не подтверждён";
export const formatName = (v: string) =>
  ({ remote: "Удалённо", hybrid: "Гибрид", office: "В офисе" })[v] || v;
export const statusName = (v: string) =>
  ({
    sent: "Отправлено",
    viewed: "Просмотрено",
    accepted: "Принято",
    declined: "Отклонено",
    withdrawn: "Отозвано",
    reviewing: "На рассмотрении",
    interview: "Собеседование",
    rejected: "Отказ",
  })[v] || v;
export const money = (v: number) => new Intl.NumberFormat("ru-RU").format(v);
export const date = (v: number | null) =>
  v ? new Date(v * 1000).toLocaleDateString("ru-RU") : "—";
