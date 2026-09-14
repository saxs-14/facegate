const API_BASE = "https://facegate-607032555709.us-central1.run.app";

export interface Person {
  id: number;
  name: string;
  category: string;
  consent_given: boolean;
  created_at: string;
}

export interface AccessEvent {
  id: number;
  person_id: number | null;
  recognized_name: string | null;
  confidence_distance: number;
  event_type: string;
  timestamp: string;
}

export interface DashboardSummary {
  total_enrolled: number;
  total_events: number;
  unknown_events: number;
  events_today: number;
  confidence_threshold: number;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => res.statusText);
    throw new Error(body || res.statusText);
  }
  return res.json();
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export const api = {
  health: () => fetch(`${API_BASE}/api/health`).then((r) => json<{ status: string }>(r)),

  login: (username: string, password: string) =>
    fetch(`${API_BASE}/api/auth/login?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`, {
      method: "POST",
    }).then((r) => json<{ access_token: string }>(r)),

  summary: (token: string) =>
    fetch(`${API_BASE}/api/dashboard/summary`, { headers: authHeaders(token) }).then((r) => json<DashboardSummary>(r)),

  events: (token: string) =>
    fetch(`${API_BASE}/api/events`, { headers: authHeaders(token) }).then((r) => json<AccessEvent[]>(r)),

  exportEvents: async (token: string) => {
    const res = await fetch(`${API_BASE}/api/events/export`, { headers: authHeaders(token) });
    if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "facegate_events.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  listEnrolled: (token: string) =>
    fetch(`${API_BASE}/api/enroll`, { headers: authHeaders(token) }).then((r) => json<Person[]>(r)),

  enroll: (token: string, name: string, category: string, consent: boolean, file: File) => {
    const form = new FormData();
    form.set("name", name);
    form.set("category", category);
    form.set("consent_given", String(consent));
    form.set("file", file);
    return fetch(`${API_BASE}/api/enroll`, { method: "POST", headers: authHeaders(token), body: form }).then((r) =>
      json<Person>(r)
    );
  },

  deletePerson: (token: string, id: number) =>
    fetch(`${API_BASE}/api/enroll/${id}`, { method: "DELETE", headers: authHeaders(token) }).then((r) => json(r)),

  recognize: (token: string, eventType: string, file: File) => {
    const form = new FormData();
    form.set("event_type", eventType);
    form.set("file", file);
    return fetch(`${API_BASE}/api/recognize`, { method: "POST", headers: authHeaders(token), body: form }).then((r) =>
      json<AccessEvent>(r)
    );
  },
};
