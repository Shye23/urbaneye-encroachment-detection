# UrbanEye

UrbanEye is a satellite-based change-detection and potential encroachment
screening system. It contains:

- A Python ML pipeline for aligned satellite-image change detection.
- A Bhoonidhi provider adapter for catalogue search and scene downloads.
- A Django/Celery backend that submits and tracks detection jobs.
- A React/Vite portal for AOI selection, detection monitoring, and PDF reports.

The system is a decision-support tool. A detected change is **not** a legal
finding of encroachment. Results require official GIS review, cadastral
verification, and field/legal verification.

## Repository layout

```text
UrbanEye/
├── inference/                  # Reusable ML pipeline and Bhoonidhi adapter
├── models/                     # PyTorch model definitions
├── preprocessing/              # Training/preprocessing utilities
├── training/                   # Training scripts and optional checkpoints
├── requirements.txt            # ML/Python dependency baseline
├── urbaneye_zip/
│   ├── backend/                # Django API, Celery task, PostgreSQL models
│   └── urbaneye-frontend/      # React/Vite portal
├── raw data/                   # Local imagery; do not commit bulk data
├── processed_data/             # Local intermediate data; do not commit
├── outputs/                    # Local pipeline outputs; do not commit
└── results/                    # Local reports/results; do not commit
```

## Prerequisites

Each teammate needs:

- Windows 10/11 PowerShell.
- Git.
- Python 3.13 (the current environments use Python 3.13).
- Node.js 20.19+ or Node.js 22.12+.
- PostgreSQL 17 running on port `5432`.
- Redis-compatible service on port `6379`.
  - On Windows, Memurai is supported by the current Celery configuration.
- A Bhoonidhi account if live satellite downloads are required.
- NVIDIA GPU/CUDA is recommended for practical inference, but CPU execution
  may be possible for small test scenes and will be slower.

Never commit Bhoonidhi credentials, JWTs, database passwords, Django secret
keys, or downloaded satellite products.

## Clone the repository

```powershell
git clone <YOUR-GITHUB-URL>
Set-Location UrbanEye
```

## 1. Create the ML environment

Create the ML environment at the path expected by the backend, or configure
the path explicitly later:

```powershell
py -3.13 -m venv urban_env
.\urban_env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install a PyTorch build appropriate for the teammate's hardware. For example,
use the official selector at <https://pytorch.org/get-started/locally/>.
The trained model checkpoint must be available at:

```text
training\checkpoints\snunet\baseline\best_model.pth
```

If checkpoints are stored outside GitHub, set `URBANEYE_CHECKPOINT` when
starting the worker. The repository ignore rules exclude `.pth` files by
default; use Git LFS if the team wants to store a checkpoint in GitHub:

```powershell
git lfs install
git lfs track "training/checkpoints/**/*.pth"
git add .gitattributes
git add -f training/checkpoints/snunet/baseline/best_model.pth
```

The default live worker expects the SNUNet checkpoint shown above. Do not
commit large datasets or generated scene files.

## 2. Install and configure PostgreSQL

Install PostgreSQL 17 and ensure the PostgreSQL service is running on port
`5432`. Create a database:

```sql
CREATE DATABASE urbaneye_db;
```

The configured database user must have access to this database. The backend
defaults to PostgreSQL; SQLite is only an explicit development fallback and
should not be used for the intended deployment.

## 3. Install and configure the backend

```powershell
Set-Location urbaneye_zip\backend
py -3.13 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with local values:

```dotenv
SECRET_KEY=replace-with-a-long-random-local-secret
DEBUG=True

DB_NAME=urbaneye_db
DB_USER=postgres
DB_PASSWORD=replace-with-local-postgres-password
DB_HOST=127.0.0.1
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/1

URBANEYE_ML_ROOT=E:/UrbanEye
URBANEYE_ML_PYTHON=E:/UrbanEye/urban_env/Scripts/python.exe
URBANEYE_ML_RUNNER=E:/UrbanEye/inference/run_live_detection.py
```

Use forward slashes in `.env` paths, or escape Windows backslashes.
`URBANEYE_ML_ROOT` must point to the cloned ML project root on that computer.

Apply migrations and create an administrator:

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
```

The user must have the `ADMIN` role to submit detection jobs. If an existing
user was created with the default citizen role, update it in the Django shell:

```powershell
python manage.py shell -c "from accounts.models import User; u=User.objects.get(username='YOUR_USERNAME'); u.role='ADMIN'; u.is_staff=True; u.save()"
```

## 4. Start the services

Use separate PowerShell windows.

### Memurai/Redis

```powershell
Get-Service Memurai
Test-NetConnection 127.0.0.1 -Port 6379
```

If using another Redis installation, keep `REDIS_URL` consistent with it.

### Django

```powershell
Set-Location urbaneye_zip\backend
.\env\Scripts\Activate.ps1
Remove-Item Env:DB_ENGINE -ErrorAction SilentlyContinue
python manage.py runserver 127.0.0.1:8000
```

### Celery worker

The Bhoonidhi variables must be set in the same PowerShell process that
starts Celery:

```powershell
Set-Location urbaneye_zip\backend
.\env\Scripts\Activate.ps1

$env:BHOONIDHI_USER_ID = "your-bhoonidhi-user-id"
$env:BHOONIDHI_PASSWORD = "your-bhoonidhi-password"

.\env\Scripts\celery.exe `
  -A urbaneye_backend `
  worker `
  --loglevel=INFO `
  --pool=solo
```

The worker should report that it connected to Redis and is ready. It launches
the ML runner in the separate `urban_env` environment.

### React portal

```powershell
Set-Location urbaneye_zip\urbaneye-frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173>.

## Detection workflow

1. Sign in with an `ADMIN` or `DEPARTMENT` account.
2. Open **Detection**.
3. Click two opposite corners on the map to define an AOI.
4. Select baseline and comparison dates.
5. Select `ResourceSat-2_LISS4-MX70_L2`.
6. Submit the job.
7. Keep the Celery terminal open and watch the job progress.
8. Open **Reports** to view job history and download PDF reports.

The worker searches Bhoonidhi in windows no longer than 366 days, downloads
usable scenes, extracts `BAND2.tif`, `BAND3.tif`, and `BAND4.tif`, normalizes
and aligns them, then runs the ML pipeline.

## Troubleshooting

### Job stays at `PENDING`

The Celery worker is not running, is connected to a different Redis database,
or was started without the same `REDIS_URL` as Django. Restart the worker and
look for a `ready` message.

### Job stays at `RUNNING` at 10%

The worker has started the subprocess but may have stopped. Inspect the
Celery terminal and restart the worker if it is no longer running.

### Bhoonidhi returns HTTP 401

Set `BHOONIDHI_USER_ID` and `BHOONIDHI_PASSWORD` in the worker's PowerShell
session. Never put them in Git or send them in chat.

### Bhoonidhi returns HTTP 404

The catalogue can contain stale products. The worker skips unavailable
products and tries another matching scene. If all candidates fail, use a
different date range or AOI.

### No valid pixels or no change regions

The selected AOI may not contain valid pixels in one scene, or the model may
find no change that survives postprocessing. Try a smaller known-covered AOI
or a nearby date pair. A no-change result should not be interpreted as proof
that no encroachment exists.

### PostgreSQL connection failure

```powershell
Test-NetConnection 127.0.0.1 -Port 5432
```

Check the PostgreSQL service, database name, username, password, and `.env`.

## What to commit and what not to commit

Commit:

- `inference/`, `models/`, `preprocessing/`, and training scripts.
- Django source, migrations, and configuration.
- React source, `package.json`, and `package-lock.json`.
- `requirements.txt` files.
- Safe configuration templates such as `.env.example`.
- Documentation and small, non-sensitive test fixtures.
- Model checkpoints only if the team agrees to store them with Git LFS or a
  release asset.

Do not commit:

- `urban_env/`, `urbaneye_zip/backend/env/`, or any virtual environment.
- `urbaneye_zip/urbaneye-frontend/node_modules/`.
- `urbaneye_zip/backend/.env`.
- `db.sqlite3`, `media/`, job workspaces, logs, caches, and `dist/`.
- Bhoonidhi credentials, tokens, or authorization headers.
- Bulk satellite imagery, downloaded archives, temporary rasters, or generated
  reports.
- PostgreSQL data directories or Redis/Memurai files.

## Suggested first collaboration workflow

```powershell
git checkout -b feature/your-change
git status
git add inference models preprocessing training urbaneye_zip/backend urbaneye_zip/urbaneye-frontend requirements.txt README.md .gitignore
git commit -m "Describe the change"
git push -u origin feature/your-change
```

Open a pull request rather than pushing directly to the default branch.

## Recommended GitHub contents

The first push should contain the source/configuration tree below:

```text
README.md
.gitignore
requirements.txt
inference/
models/
preprocessing/
training/*.py
training/**/*.csv
training/**/*.txt
urbaneye_zip/backend/
urbaneye_zip/urbaneye-frontend/src/
urbaneye_zip/urbaneye-frontend/public/
urbaneye_zip/urbaneye-frontend/package.json
urbaneye_zip/urbaneye-frontend/package-lock.json
urbaneye_zip/urbaneye-frontend/vite.config.*
```

Do not add the following even if they exist locally:

```text
urban_env/
urbaneye_zip/backend/env/
urbaneye_zip/urbaneye-frontend/node_modules/
urbaneye_zip/backend/.env
urbaneye_zip/backend/db.sqlite3
urbaneye_zip/backend/media/
raw data/
processed_data/
outputs/
results/
downloaded_scenes*/
```

If a teammate needs a reproducible demo without Bhoonidhi credentials,
share a small sanitized fixture separately or create a private GitHub
release asset. Do not put government or user data in a public repository.
