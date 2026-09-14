import { Link } from "react-router-dom";

const FEATURES = [
  { title: "Face enrollment", desc: "Register visitors or staff with explicit consent, on the spot." },
  { title: "Face recognition", desc: "Matches a live photo against enrolled identities at the door." },
  { title: "Unknown-person alerts", desc: "Flags anyone who doesn't match an enrolled identity." },
  { title: "Check-in / check-out log", desc: "Full searchable access history with timestamps." },
  { title: "Configurable confidence", desc: "Admins tune how strict the match threshold is." },
  { title: "Data deletion", desc: "Remove an enrolled identity's record on request." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between px-6 py-5 max-w-6xl mx-auto">
        <div className="flex items-center gap-2 font-semibold text-lg">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-indigo-500" />
          FaceGate
        </div>
        <Link to="/app" className="rounded-lg bg-indigo-600 hover:bg-indigo-500 transition px-4 py-2 text-sm font-medium">
          Open dashboard
        </Link>
      </header>

      <main className="max-w-6xl mx-auto px-6">
        <section className="py-16 text-center">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight">
            Privacy-conscious <span className="text-indigo-400">visitor access</span> management
          </h1>
          <p className="mt-5 text-slate-400 max-w-2xl mx-auto text-lg">
            Replace the paper register with face-based check-in — enrolled with consent, matched with a
            configurable confidence threshold, fully auditable.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Link to="/app" className="rounded-lg bg-indigo-600 hover:bg-indigo-500 transition px-5 py-3 font-medium">
              Try the live demo
            </Link>
          </div>
        </section>

        <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 py-8">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
              <h3 className="font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm text-slate-400">{f.desc}</p>
            </div>
          ))}
        </section>

        <section className="py-16 rounded-xl border border-amber-500/30 bg-amber-500/5 p-6">
          <h2 className="text-lg font-bold text-amber-400 mb-2">Privacy notice</h2>
          <ul className="text-sm text-slate-300 space-y-1.5 list-disc pl-5">
            <li>Enrollment requires explicit, recorded consent before any face data is processed.</li>
            <li>The original uploaded photo is never stored — only a numeric face-recognition model derived from it.</li>
            <li>Face matching is probabilistic. It is <strong>not perfect</strong> — a confidence threshold is
              admin-configurable, and every match is logged for audit.</li>
            <li>Enrolled people can be removed (data deletion) at any time from the admin dashboard.</li>
            <li>Deployers are responsible for signage and legal compliance for biometric processing in their
              jurisdiction — see the README "Privacy considerations".</li>
          </ul>
        </section>

        <section className="py-16 grid sm:grid-cols-2 gap-8">
          <div>
            <h2 className="text-2xl font-bold mb-3">Who it's for</h2>
            <ul className="text-slate-400 space-y-1.5 text-sm">
              <li>Offices replacing sign-in sheets</li>
              <li>Schools managing visitor access</li>
              <li>Residential estates and gated communities</li>
              <li>Warehouses and small businesses</li>
              <li>Events needing fast, contactless check-in</li>
            </ul>
          </div>
          <div>
            <h2 className="text-2xl font-bold mb-3">Pricing model</h2>
            <ul className="text-slate-400 space-y-1.5 text-sm">
              <li>Monthly subscription per site</li>
              <li>Per-location pricing for multi-site organizations</li>
              <li>One-time installation fee</li>
              <li>Enterprise package with SSO and multi-role access</li>
            </ul>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        FaceGate — visitor access MVP. Recognition is probabilistic, not infallible.
      </footer>
    </div>
  );
}
