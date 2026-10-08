# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Temporary: design phase

At the start of every new chat, read `README.md` (project goal and flow), `TIMELINE.md` (build plan with checkboxes) and `OPEN_DECISIONS.md` (unresolved design questions). Nothing is final: the existing code, the timeline and the design are all open to change, so don't treat any of them as settled. Remove this section once project design is finished.

## Commands

Python 3.12 + [uv](https://docs.astral.sh/uv/). No tests, linter, or formatter are configured yet.

```bash
cp .env.example .env                 # then set DATABASE_URL (postgresql+psycopg://...); needs a running Postgres
uv sync                              # install deps
uv run fastapi dev src/main.py       # dev server, http://localhost:8000 (docs at /docs)
docker compose up --build            # run in Docker (CMD is `fastapi run`)
```

The FastAPI entrypoint is `src.main:app` (set in `pyproject.toml`); run commands from the repo root since modules import as `src.*`.

## Architecture

Book Guide is meant to be an AI agent for reading PDFs section-by-section (see README for the goal). Currently only the ingestion API exists; there is no agent/retrieval code yet.

- `src/main.py` — creates the app, mounts routers, creates tables on startup (`create_all`; Alembic is planned but not set up, so schema changes to existing tables aren't applied).
- `src/config.py` — `BASE_DIR` and pydantic-settings `Settings` (`database_url`, read from `.env`); use `get_settings()`.
- `src/database.py` — SQLModel engine on Postgres from `DATABASE_URL` (driver is psycopg 3, so the URL scheme must be `postgresql+psycopg://`); `SessionDep` is the injected session dependency.
- `src/books/models.py` — `Book` (uploaded file) and `BookToc` (self-referential tree via `parent_id`/`children`, with `start_page`, `end_page`, `level`; cascade-deleted with the book).
- `src/books/router.py` — upload (`POST /books/`) stores the PDF as `uploads/<uuid>.pdf`, parses it with PyMuPDF (`doc.get_toc()`), and saves TOC rows. Delete removes the DB row and the file. `src/books/service.py` is currently empty.
- Planned (per README): `BookToc` becomes `BookSection`; a PDF with no TOC gets no auto-created sections, and pages/ranges are read directly from the stored file.

## Work-in-progress caveats

The router is mid-refactor and out of sync with the models: `create_book` builds `BookToc(page_number=..., page_level=...)` but the model fields are `start_page`, `end_page`, `level` (and `end_page` is never computed, `parent_id` never set). It also passes `details=` instead of `detail=` to `HTTPException` in the invalid-PDF handler. `delete_book` resolves `BASE_DIR / book.file_path`, while `file_path` is stored as an absolute path (works only because absolute paths override in `pathlib`). Verify these before relying on upload behavior.

`uploads/` and `.env` are local state; don't commit their contents (`data/` is a leftover from SQLite). Commit `.env.example` only.
