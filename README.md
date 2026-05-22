# Votestack3

Flask-based voting app. Fixed version of Votestack2 — fully unified on SQLite,
DB schema created automatically on startup (no more missing-table crashes on Render).

## What changed from Votestack2

| Issue | Fix |
|---|---|
| `no such table: settings` on every cold start | `app.py` now calls `create_tables()` + `migrate_files_to_db()` inside `with app.app_context()` before the first request |
| `load_role()` read from a flat file while `get_current_role()` queried SQLite | Removed the flat-file path; everything reads/writes the `settings` table |
| `Procfile` said `gunicorn app` (no `:app`) | Fixed to `gunicorn app:app` |
| Voters stored only in `usernames.txt` | All voter CRUD goes through the `users` table |

## Local development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Deploy on Render

1. Push this repo to GitHub.
2. Create a new **Web Service** on Render, connect the repo.
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `gunicorn app:app`
5. Add a **Persistent Disk** (mount path `/data`, any size) and set the
   environment variable `DB_PATH=/data/votestack3.db` if you want data to
   survive restarts (otherwise the DB resets on each deploy on the free tier).
6. Optionally set `SECRET_KEY` to a long random string in Render environment vars.

## Notes on Render's ephemeral filesystem

On Render's free tier, the disk resets on every redeploy. To keep voter
registrations and votes across deploys, add a **Persistent Disk** in the
Render dashboard and update `DB_FILE` in `app.py` / `init_db.py` to point
to the mounted path (e.g. `/data/votestack3.db`).
