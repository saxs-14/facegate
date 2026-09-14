import { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { api, DashboardSummary, AccessEvent, Person } from "../lib/api";
import KpiCard from "../components/KpiCard";

export default function Dashboard() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem("facegate_token"));
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [events, setEvents] = useState<AccessEvent[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  const [enrollName, setEnrollName] = useState("");
  const [enrollFile, setEnrollFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [recognizeFile, setRecognizeFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<AccessEvent | null>(null);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const [s, e, p] = await Promise.all([api.summary(token), api.events(token), api.listEnrolled(token)]);
      setSummary(s);
      setEvents(e);
      setPeople(p);
    } catch {
      /* backend offline or token expired - surfaced via apiOnline / login gate */
    }
  }, [token]);

  useEffect(() => {
    api.health().then(() => setApiOnline(true)).catch(() => setApiOnline(false));
    refresh();
  }, [refresh]);

  const login = async () => {
    setLoginError(null);
    try {
      const { access_token } = await api.login(username, password);
      sessionStorage.setItem("facegate_token", access_token);
      setToken(access_token);
    } catch (e) {
      setLoginError(e instanceof Error ? e.message : "Login failed");
    }
  };

  const logout = () => {
    sessionStorage.removeItem("facegate_token");
    setToken(null);
  };

  const doEnroll = async () => {
    if (!token || !enrollFile || !enrollName) return;
    setBusy(true);
    setActionError(null);
    try {
      await api.enroll(token, enrollName, "visitor", consent, enrollFile);
      setEnrollName("");
      setEnrollFile(null);
      setConsent(false);
      await refresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Enrollment failed");
    } finally {
      setBusy(false);
    }
  };

  const doRecognize = async (eventType: "check_in" | "check_out") => {
    if (!token || !recognizeFile) return;
    setBusy(true);
    setActionError(null);
    try {
      const result = await api.recognize(token, eventType, recognizeFile);
      setLastResult(result);
      await refresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Recognition failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <Link to="/" className="flex items-center gap-2 font-semibold">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-indigo-500" />
          FaceGate
        </Link>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-2">
            <span className={`inline-block h-2 w-2 rounded-full ${apiOnline ? "bg-emerald-500" : "bg-red-500"}`} />
            {apiOnline === null ? "Checking..." : apiOnline ? "Backend online" : "Backend offline"}
          </span>
          {token && (
            <button onClick={logout} className="rounded-lg border border-slate-700 px-3 py-1.5 hover:border-slate-500">
              Log out
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        {!apiOnline && apiOnline !== null && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm">
            Can't reach the backend at <code>/api</code>. Start it with <code>uvicorn app.main:app --reload</code> in{" "}
            <code>backend/</code>.
          </div>
        )}

        <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard label="Enrolled identities" value={summary?.total_enrolled ?? "-"} />
          <KpiCard label="Total events" value={summary?.total_events ?? "-"} />
          <KpiCard label="Unknown-person events" value={summary?.unknown_events ?? "-"} accent="alert" />
          <KpiCard label="Events today" value={summary?.events_today ?? "-"} />
        </section>

        {!token ? (
          <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 max-w-sm">
            <h2 className="font-semibold mb-4">Admin login</h2>
            <div className="space-y-3">
              <input
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm"
              />
              <input
                placeholder="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm"
              />
              <button
                onClick={login}
                className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 transition px-4 py-2 text-sm font-medium"
              >
                Log in
              </button>
              {loginError && <p className="text-red-400 text-xs">{loginError}</p>}
              <p className="text-xs text-slate-500">
                Demo credentials: <code>admin</code> / <code>SafeGate2026!</code> (see backend/.env.example)
              </p>
            </div>
          </section>
        ) : (
          <>
            <section className="grid sm:grid-cols-2 gap-6">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
                <h2 className="font-semibold mb-4">Enroll a person</h2>
                <div className="space-y-3">
                  <input
                    placeholder="Full name"
                    value={enrollName}
                    onChange={(e) => setEnrollName(e.target.value)}
                    className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm"
                  />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setEnrollFile(e.target.files?.[0] ?? null)}
                    className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-200"
                  />
                  <label className="flex items-center gap-2 text-sm text-slate-300">
                    <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                    This person has given explicit consent to be enrolled
                  </label>
                  <button
                    disabled={!enrollName || !enrollFile || !consent || busy}
                    onClick={doEnroll}
                    className="rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 transition px-4 py-2 text-sm font-medium"
                  >
                    {busy ? "Working..." : "Enroll"}
                  </button>
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
                <h2 className="font-semibold mb-4">Test recognition</h2>
                <div className="space-y-3">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setRecognizeFile(e.target.files?.[0] ?? null)}
                    className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-slate-200"
                  />
                  <div className="flex gap-2">
                    <button
                      disabled={!recognizeFile || busy}
                      onClick={() => doRecognize("check_in")}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 transition px-4 py-2 text-sm font-medium"
                    >
                      Check in
                    </button>
                    <button
                      disabled={!recognizeFile || busy}
                      onClick={() => doRecognize("check_out")}
                      className="rounded-lg border border-slate-700 hover:border-slate-500 disabled:opacity-40 transition px-4 py-2 text-sm font-medium"
                    >
                      Check out
                    </button>
                  </div>
                  {lastResult && (
                    <p className="text-sm">
                      {lastResult.recognized_name ? (
                        <>
                          Matched <strong>{lastResult.recognized_name}</strong> (distance{" "}
                          {lastResult.confidence_distance})
                        </>
                      ) : (
                        <span className="text-amber-400">Unknown person (no match above confidence threshold)</span>
                      )}
                    </p>
                  )}
                </div>
              </div>
            </section>

            {actionError && (
              <p className="text-sm text-red-400 rounded-lg border border-red-500/40 bg-red-500/10 p-3">
                {actionError}
              </p>
            )}

            <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
              <h2 className="font-semibold mb-4">Enrolled people ({people.length})</h2>
              {people.length === 0 ? (
                <p className="text-sm text-slate-500">No one enrolled yet.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-slate-500 border-b border-slate-800">
                      <th className="py-2 pr-4">Name</th>
                      <th className="py-2 pr-4">Category</th>
                      <th className="py-2 pr-4">Enrolled</th>
                      <th className="py-2 pr-4" />
                    </tr>
                  </thead>
                  <tbody>
                    {people.map((p) => (
                      <tr key={p.id} className="border-b border-slate-800/60">
                        <td className="py-2 pr-4">{p.name}</td>
                        <td className="py-2 pr-4 capitalize">{p.category}</td>
                        <td className="py-2 pr-4 text-slate-500">{new Date(p.created_at).toLocaleDateString()}</td>
                        <td className="py-2 pr-4">
                          <button
                            onClick={async () => {
                              await api.deletePerson(token, p.id);
                              refresh();
                            }}
                            className="text-red-400 hover:text-red-300 text-xs"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}

        {token && (
        <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Access event history</h2>
            <button
              onClick={() => api.exportEvents(token)}
              className="text-sm rounded-lg border border-slate-700 hover:border-slate-500 transition px-3 py-1.5"
            >
              Export CSV
            </button>
          </div>
          {events.length === 0 ? (
            <p className="text-sm text-slate-500">No events recorded yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800">
                  <th className="py-2 pr-4">Name</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Distance</th>
                  <th className="py-2 pr-4">Time</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id} className="border-b border-slate-800/60">
                    <td className="py-2 pr-4">{e.recognized_name ?? <span className="text-amber-400">Unknown</span>}</td>
                    <td className="py-2 pr-4 capitalize">{e.event_type.replace("_", " ")}</td>
                    <td className="py-2 pr-4">{e.confidence_distance}</td>
                    <td className="py-2 pr-4 text-slate-500">{new Date(e.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
        )}
      </main>
    </div>
  );
}
