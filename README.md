# HoverLearn

A lightweight Django app for learning from videos with a dark, Netflix-style UI.

Features
- Search videos by title from the Navbar
- Per-user Video Notes (with optional timestamps) saved via HTMX
- Watch history and resume (periodic client-side updates + resume on load)
- Responsive video grid and player UI with interactive subtitles (hover to get definitions)
- HTMX-powered endpoints for fast, in-page actions (save/delete notes)

Table of Contents
- [Quick Start](#quick-start) ✅
- [Environment & Config](#environment--config) ⚙️
- [Database & Migrations](#database--migrations) 🗄️
- [Key Files & Implementation Notes](#key-files--implementation-notes) 🔧
- [HTMX & JavaScript Behaviour](#htmx--javascript-behaviour) 🧩
- [Manual Test Checklist](#manual-test-checklist) ✅
- [Admin Setup](#admin-setup) 🔐
- [Security & Next Steps](#security--next-steps) 🔒
- [Troubleshooting](#troubleshooting) ⚠️
- [License & Credits](#license--credits) 📝

---

## Quick Start

Requirements: Python 3.11+, pip, virtualenv

1. Clone & create a venv

```bash
git clone <repo-url> hoverl
cd hoverl
python -m venv .venv
.\.venv\Scripts\activate    # Windows PowerShell
pip install -r requirements.txt
```

2. Create a `.env` (recommended) with at minimum:

```env
DJANGO_SECRET_KEY=changeme
DEBUG=True
GEMINI_API_KEY=your_api_key_here   # Optional: move this out of source
```

3. Run migrations and create superuser

```bash
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
```

4. Run the dev server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in.

---

## Environment & Config
- Keep any API keys (e.g., `GEMINI_API_KEY`) and `SECRET_KEY` out of source; use environment variables or a `.env` file.
- Use `DEBUG=False` in production and configure `ALLOWED_HOSTS`.

---

## Database & Migrations
- Models added:
  - `VideoNote` (user, video, content, timestamp, created_at)
  - `WatchHistory` (user, video, last_position, updated_at)
- If you update models, run:

```bash
python manage.py makemigrations core
python manage.py migrate
```

---

## Key Files & Implementation Notes
- `core/models.py`
  - `VideoNote`, `WatchHistory` implemented
- `core/views.py`
  - `home(request)` supports `?q=` to search videos (`title__icontains`)
  - `watch_video(request, video_id)` passes `notes` and `last_position` to the template
  - `save_note(request, video_id)` (HTMX POST) creates `VideoNote` and returns notes partial
  - `delete_note(request, note_id)` (HTMX POST) deletes a note
  - `update_history(request)` (POST) updates/creates `WatchHistory`
- `hoverlearn/urls.py`
  - Routes added: `video/<id>/save-note/`, `note/<id>/delete/`, `update-history/`
- Templates:
  - `templates/base.html` — search form added to navbar (styled for dark theme)
  - `templates/player.html` — notes pane (hidden by default), JS for progress updates & resume, fullscreen behavior handling
  - `templates/partials/video_notes_list.html` — partial used by HTMX to render the notes list
  - `templates/saved_list.html` — added "My Video Notes" section with links to jump to timestamps

---

## HTMX & JavaScript behaviour
- The app uses HTMX for in-page updates (notes save/delete) to avoid full page reloads.
- Notes `save_note` endpoint expects `POST` with `content` and optional `timestamp` and returns rendered partial.
- `update_history` is called every 5 seconds from the player JS to persist `current_time`. On unload/visibilitychange a `sendBeacon` is attempted to capture final position.
- Clicking a note timestamp seeks the player via delegated event listeners or falls back to `?t=` on the watch page.
- Fullscreen behaviour: by default overlays are hidden while in fullscreen (user preference). You can toggle or change this behavior in `player.html` in the `fullscreenchange` handler.

---

## Manual Test Checklist (Recommended)
1. Migrations: `makemigrations` & `migrate` (ensure `VideoNote` and `WatchHistory` tables exist).
2. Login with a created user via `/login/`.
3. Search: Use the navbar search and confirm results filter by title.
4. Notes: Open a video `/watch/<id>/`:
   - Click the **📝 Notes** button (appears on video pages) to open the pane.
   - Add a note (optionally click **Save at current time**) — the notes list should update via HTMX.
   - Click a timestamp in the notes list to jump the player.
   - Delete a note using the Delete button (HTMX should remove it).
5. Resume: Play, leave, come back — ensure `last_position` is used to set `video.currentTime` on load.
6. Fullscreen: Enter fullscreen and confirm behavior (overlays hidden or visible depending on code). Exit to restore overlays.

---

## Admin Setup
Add these to `core/admin.py` for quick admin management:

```python
from django.contrib import admin
from .models import VideoNote, WatchHistory

admin.site.register(VideoNote)
admin.site.register(WatchHistory)
```

---

## Security & Next Steps
- Move API keys out of code; use environment variables.
- Add rate-limiting for `update_history` to avoid DB churn from clients.
- Add unit tests for `save_note`, `delete_note`, `update_history`, and resume behaviour (I can add these).
- Consider autosaving note drafts locally and adding pagination for long note lists.

---

## Troubleshooting
- TemplateSyntaxError: check the template for invalid inline Python expressions; use `{% if %}` blocks instead.
- HTMX endpoints returning HTML: ensure correct `hx-post` and `hx-swap` usage and include `{% csrf_token %}` in forms.
- If subtitles or notes don’t show in fullscreen, check the `fullscreenchange` handler in `templates/player.html`.

---

## License & Credits
- SPDX: MIT (choose your license and include file if needed)
- Built with Django + HTMX

---

If you want, I can:
- Add a `README` section with example curl commands for the HTMX endpoints
- Create a `CONTRIBUTING.md` and basic tests for key endpoints
- Register `VideoNote`/`WatchHistory` in `admin.py` for you and run `makemigrations`/`migrate`

Tell me which follow-up you'd like and I’ll implement it next.