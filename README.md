# FaceGate

A privacy-conscious facial recognition visitor/access management MVP: enroll people with
explicit consent, then check them in and out by matching a photo against enrolled faces.

## Problem statement

Organizations manage visitor access with paper registers or nothing at all — slow, easy to
falsify, and impossible to search or audit.

## Solution

Admins enroll people (with recorded consent) via a photo. At the door, a new photo is
matched against enrolled identities; unknown faces are flagged. Every check-in/out and every
unknown-person event is logged and exportable.

## Features

- Admin authentication (JWT) with rate-limited login
- Face enrollment with mandatory consent checkbox
- Face detection (OpenCV DNN) + recognition (OpenCV LBPH)
- Unknown-person detection via a configurable confidence threshold
- Check-in / check-out event logging with CSV export
- Data deletion (right-to-erasure) for enrolled identities
- Audit log of admin actions (enroll, delete)
- Demo mode: enroll and recognize using your own webcam/uploaded photo — no stock photos
  of real people are bundled with this project (see Privacy considerations)

## Architecture

```text
frontend (React/Vite/TS/Tailwind)  ->  backend (FastAPI, JWT auth)  ->  SQLite
                                              |
                                     OpenCV DNN face detector
                                     + OpenCV LBPH face recognizer
```

## Technology stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, OpenCV-contrib (DNN + `cv2.face` LBPH),
  passlib/bcrypt, python-jose (JWT)
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Face detector**: OpenCV DNN res10 SSD (Caffe, ~5MB)
- **Face recognizer**: LBPH (Local Binary Patterns Histograms) — a classical algorithm
  bundled with opencv-contrib, chosen over `face_recognition`/dlib (needs a C++ build
  toolchain) and over deep embeddings like FaceNet/ArcFace (multi-hundred-MB models) —
  the right trade-off for an MVP with a handful of enrolled identities, not for
  large-scale (1000s of identities) production deployment.

## Folder structure

```text
facegate/
├── backend/
│   ├── app/            # FastAPI app, auth, face engine, routers
│   ├── models/          # face detector prototxt + caffemodel
│   └── tests/
├── frontend/
│   └── src/              # Landing page + admin dashboard
├── docker-compose.yml
└── README.md
```

## Installation

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env
```

Face detector model files must exist at `backend/models/deploy.prototxt` and
`backend/models/res10_300x300_ssd_iter_140000_fp16.caffemodel`. If missing:

```bash
curl -L -o models/deploy.prototxt https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt
curl -L -o models/res10_300x300_ssd_iter_140000_fp16.caffemodel https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20180205_fp16/res10_300x300_ssd_iter_140000_fp16.caffemodel
```

### Frontend

```bash
cd frontend && npm install
```

## Environment variables

See `backend/.env.example` — notably `JWT_SECRET` (change in production),
`DEFAULT_ADMIN_USERNAME`/`DEFAULT_ADMIN_PASSWORD` (seeded admin account), and
`RECOGNITION_CONFIDENCE_THRESHOLD` (LBPH distance — lower is stricter).

## Running locally

```bash
# Terminal 1
cd backend && venv\Scripts\activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173, then `/app` to log in (demo credentials below).

### Docker

```bash
docker compose up --build
```

## Demo instructions

1. Log in with the seeded demo admin: **username `admin`, password `SafeGate2026!`**
   (change `DEFAULT_ADMIN_PASSWORD` before any real deployment).
2. Enroll yourself: upload a clear front-facing photo, tick the consent box, submit.
3. Upload a second photo of yourself under "Test recognition" and click Check in — it
   should match with a low distance value.
4. Upload a photo of someone else (or any non-matching image with a detectable face) to
   see the "unknown person" path.

No stock photos of real people are bundled with this repository, by design — see Privacy
considerations below.

## API documentation

Interactive docs at `/docs`. Key endpoints:

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/login` | — | Returns a JWT (rate-limited: 5 attempts/60s/IP) |
| GET/POST | `/api/enroll` | Bearer | List / create enrolled identities |
| DELETE | `/api/enroll/{id}` | Bearer | Delete an enrolled identity |
| POST | `/api/recognize` | Bearer | Match a photo, log a check-in/check-out/unknown event |
| GET | `/api/events` | — | Event history |
| GET | `/api/events/export` | — | CSV export |
| GET | `/api/dashboard/summary` | — | Aggregate KPIs |

## Database

SQLite (`facegate.db`): `admin_users`, `enrolled_persons`, `access_events`, `audit_logs`.

## Security considerations

- Passwords hashed with bcrypt (never stored/logged in plaintext)
- JWT-based auth on all enrollment/recognition/admin endpoints
- Login endpoint rate-limited (in-memory, per-IP) against brute force
- Upload content-type and size validated server-side
- CORS restricted to configured origins
- No secrets in source; `.env` gitignored, `.env.example` documents required vars
- **Change `JWT_SECRET` and `DEFAULT_ADMIN_PASSWORD` before any real deployment** — the
  shipped defaults are for local demo only

## Privacy considerations

This project treats face data as sensitive biometric information:

- Enrollment requires an explicit, recorded consent flag — the API rejects enrollment
  without it
- **The original uploaded photo is never written to disk.** It's decoded in memory, the
  face region is detected and cropped, fed into the recognizer's training set, and
  discarded. Only the trained LBPH model file (a numeric representation) persists.
- Deletion removes the person's database record immediately. **Limitation**: because LBPH
  trains incrementally into one shared model file, the numeric contribution of a deleted
  person isn't purged from that file until the next full re-train across remaining
  enrollees — a production system should re-train from a maintained image-free feature
  store on every deletion, or move to a per-person embedding store that supports true
  removal.
- No stock photos of real people are bundled with this repo — the demo asks you to
  enroll/test with your own photo instead, which keeps the project itself free of anyone's
  biometric data.
- Recognition is probabilistic (LBPH distance vs. a configurable threshold), not perfect —
  it will occasionally produce false matches or false unknowns. It must not be the sole
  control for high-security access.
- Deployers are responsible for visitor signage and legal compliance for biometric
  processing in their jurisdiction (e.g. POPIA in South Africa, GDPR in the EU) before
  deploying this beyond a demo.

## Limitations

- LBPH recognition accuracy degrades with lighting/angle changes and doesn't scale well
  past a few dozen identities — a production system should move to deep face embeddings
  (FaceNet/ArcFace) with a vector index.
- No liveness detection — a printed photo could currently pass recognition. A production
  deployment needs anti-spoofing (blink detection, depth camera, or a liveness model).
- Single admin role in this MVP; the `role` field exists on `AdminUser` for future
  multi-role expansion but only "admin" is currently wired up.

## Business model

**Target customers**: offices, schools, residential estates, warehouses, small businesses,
events.

**Revenue**: monthly subscription per site, per-location pricing for multi-site
organizations, one-time installation fee, enterprise package with SSO/multi-role access.

## Future improvements

- Deep-embedding recognition (FaceNet/ArcFace) for accuracy at scale
- Liveness detection / anti-spoofing
- Multi-role RBAC (admin vs. front-desk viewer)
- Email/SMS notification on unknown-person events
- True per-person data purge on deletion (embedding store instead of one shared model file)

## Screenshots

Run locally (see "Running locally"), log in with the demo admin account, and visit `/app`.
