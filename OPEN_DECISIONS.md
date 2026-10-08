# Open Decisions (temporary)

Working notes to revisit alongside the project timeline. Delete once resolved.

Status: `[ ]` open, `[x]` decided. Add the decision under each item.

## 1. Interface
API-only for now, or a web UI later? A UI affects streaming, a PDF viewer, and how the user selects the current section.
Lean: API-first, thin UI later.
- [ ] Decision:

## 2. Retrieval model
Selected section/page range is the context (no vector search). Risk: long sections exceed the context window or get expensive.
Lean: plain range-as-context; add chunking only if needed.
- [ ] Decision:

## 3. Text extraction
Extract page text at upload and store it, or read from the PDF on demand with PyMuPDF? On-demand avoids duplication; storing helps later search/caching.
- [x] Decision: keep the PDF file, read pages on demand with PyMuPDF, no text in the database. See README.

## 4. TOC fallback and `end_page`
Note: PDFs without a TOC are deferred for now (skipped until the agent parts are understood). The decisions below stay as the plan for later. What upload does with a no-TOC PDF in the meantime (reject, or accept with no sections) is not decided.
- No-TOC PDFs: one row per page, or fixed-size page blocks (e.g. 10 pages)?
- Compute `end_page` for TOC entries (next entry's start page - 1, or next sibling's).
- Set `parent_id` from heading levels.
- [x] Decision: no-TOC PDFs get no auto-created sections (page/range is the unit); `end_page` rule using the next entry's y position; `parent_id` via level stack. See README.

## 5. Agent design
- Model/SDK (Claude API?)
- Chat history per book or per session (needs new tables)?
- Web search: agent-chosen tool or user toggle?
- Streaming answers?
- [ ] Decision:

## 6. Scope and users
Single-user local tool, or multi-user with auth? "One PDF at a time": one active book, or one file per upload request?
- [ ] Decision:

## 7. Scanned PDFs
OCR for image-only PDFs, or just return a clear error when a page has no extractable text?
- [ ] Decision:

## 8. Persistence and ops
- Decided: Postgres with Alembic migrations, replacing SQLite and `create_all`. See README.
- Docker doesn't mount `data/` or `uploads/`; they're lost on container restart.
- Uploaded PDFs: local `uploads/` during development, move to S3 later (decided). Open: local S3 stand-in for dev (e.g. MinIO), local cache of fetched files.
- Decided: put file storage behind a small interface (save, read/open, delete) so the later switch to S3 touches one place instead of the routes. Not implemented yet; we finish design first.
- [ ] Decision:

## Known bugs to fix (from CLAUDE.md)
- [ ] `create_book` builds `BookToc(page_number=, page_level=)`; model fields are `start_page`, `end_page`, `level`. `end_page` and `parent_id` never set.
- [ ] `HTTPException(details=...)` should be `detail=`.
- [ ] `delete_book` joins `BASE_DIR / book.file_path` while `file_path` is stored absolute.

- [x] `.env` was tracked by git. Fixed: untracked with `git rm --cached .env`, ignored in `.gitignore`, `.env.example` added.
- [ ] `.env` is still in the history of past commits. Check `git log --oneline -- .env`; rotate `ANTHROPIC_API_KEY` if a real key was committed/pushed.
- [x] `src/config.py` now loads `.env` with pydantic-settings (`Settings.database_url`).

## Suggested order (tentative)
1. Fix upload and TOC end pages
2. Page-range text endpoint
3. Agent endpoint with chat history
4. Web search
