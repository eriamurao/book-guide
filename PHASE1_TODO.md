# Phase 1 TODO (temporary)

Ordered checklist for implementing Phase 1. Design lives in `README.md`; this file only says what to do and in what order. Delete it when Phase 1 is done.

## 0. Decide first
- [x] Switch to Postgres and add Alembic (decided, see README)

## 1. Housekeeping
- [ ] `git log --oneline -- .env` to see if the key was ever committed; rotate `ANTHROPIC_API_KEY` if it was pushed
- [ ] `git rm --cached .env`, add `.env` to `.gitignore`, add `.env.example` (key names only)
- [ ] Clean up `uploads/`: three 0-byte files from failed uploads, same books uploaded several times (keep one copy of each for testing)

## 2. Dependencies and config
- [ ] Add `pytest` (dev group) and `python-dotenv` (or pydantic-settings)
- [ ] Add a Postgres driver (psycopg) and `alembic`
- [ ] Load `.env` in `src/config.py`; add `DATABASE_URL`

## 3. Database
- [ ] Add a `db` service to `compose.yaml`, run only the DB in Docker for local dev
- [ ] Point `src/database.py` at `DATABASE_URL`
- [ ] Set up Alembic, drop `create_all` from startup

## 4. Models
- [ ] Rename `BookToc` to `BookSection` (table `book_section`)
- [ ] Fields: `id`, `book_id`, `parent_id`, `title`, `level`, `start_page`, `end_page`, `position`, `source`
- [ ] `Book` keeps only `file_name` (and `file_path`, which becomes a storage key later)
- [ ] First Alembic migration for the new schema

## 5. Section computation (pure function, no DB, no FastAPI)
- [ ] Input `doc.get_toc(simple=False)`, output sections with `end_page`, `parent_id` (via level stack), `position`
- [ ] `end_page` rule from the README: next entry at same or shallower level; no `to` / `NaN` y -> `next.start`; same start page -> `current.start`; `next.y == 0.0` -> `next.start - 1`; otherwise `next.start`; last entry -> final page; clamp to at least `start`
- [ ] Skip entries with invalid pages (`-1` / `0`)
- [ ] pytest cases: nested levels, same-page entries, `NaN` y, last entry, parent end equals max child end

## 6. Storage interface
- [ ] Small module with save / open / delete
- [ ] Local implementation writing to `uploads/` (S3 later)

## 7. Upload route (`POST /books/`)
- [ ] Use the storage interface
- [ ] Reject non-PDFs (400) and PDFs with no TOC (clear error, deferred feature)
- [ ] Build `BookSection` rows with the function from step 5
- [ ] Fix `details=` -> `detail=`
- [ ] Remove the stored file if anything fails (no more 0-byte leftovers)

## 8. Delete route
- [ ] Delete through the storage interface (no more `BASE_DIR / file_path`)
- [ ] Sections deleted with the book

## 9. Read endpoints
- [ ] List a book's sections (tree or flat with `parent_id`, ordered by `position`)
- [ ] Page text for a page or range (read from the stored PDF with PyMuPDF)

## 10. Checkpoint
- [ ] Upload a real PDF (both sample books), get back sections as `{section_title, start_page, end_page, text}`
- [ ] Update `README.md`, `TIMELINE.md`, `CLAUDE.md` to match the code
