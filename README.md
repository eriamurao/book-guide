# Book Guide

An AI agent that helps you read and understand PDFs — books, contracts, or anything else.

## Goal

Upload a PDF and read it section by section, or page by page, using the table of contents. Ask the agent to explain the part you are reading. That part is the retrieval context for the answer. If you want more context, the agent can also search the web.

## Flow

1. Upload one PDF at a time.
2. Parse it with PyMuPDF.
3. Save the table of contents in the database.
   - If the PDF has no table of contents, save it by page so you can read and discuss one page or a range of pages.

## Run locally

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run fastapi dev src/main.py
```

The API is at http://localhost:8000. Interactive docs are at http://localhost:8000/docs.

## Run with Docker

```bash
docker compose up --build
```

The API is at http://localhost:8000. See [README.Docker.md](README.Docker.md) for image build and deploy notes.

## Design decisions and discussions

Work in progress. Nothing here is final until marked **Decided**. See `TIMELINE.md` for the build plan and `OPEN_DECISIONS.md` for the working checklist.

### Decided

**Rename `BookToc` to `BookSection`.**
- Why: the fallback for PDFs without a TOC produces sections that are not TOC entries, so "section" covers both.
- Tradeoff: a rename touches the model, table name and router; nothing else depends on it yet, so it is cheapest now.

**`Book` keeps only `file_name` (no `title`, no `page_count` for now).**
- Why: the user uploaded a file and sees its file name. A title taken from PDF metadata is invisible to them and can differ from, or be missing next to, the file name, which would be confusing.
- Tradeoff: no cleaner display title and no cached page count. Both can be added later without breaking anything; `page_count` can be read from the PDF when needed.

**`end_page` is computed from the next entry's page and y position.**
- Source: `doc.get_toc(simple=False)`, which gives `[level, title, page, dest]`. `dest['to']` is a `Point` (y measured from the top of the page; x and y can be `NaN`). `dest['page']` is 0-indexed, the entry's own `page` is 1-indexed.
- For each entry, find the *next entry at the same or a shallower level*. Then:
  1. No `to`, or `NaN` y: `end = next.start` (keep the page rather than lose text).
  2. `next.start == current.start`: `end = current.start`.
  3. `next.y == 0.0` (next section starts at the very top of its page): `end = next.start - 1`.
  4. Otherwise: `end = next.start` (the boundary page is shared).
  5. The last entry ends at the final page. Clamp `end` to at least `start`.
- Nested levels: a section and its last subsection both look for the same next entry, so they end on the same page. A parent's `end_page` always equals the largest `end_page` among its children (testable invariant). The same pass sets `parent_id` using a stack of open sections by level.
- Tradeoff: the strict `y == 0.0` check treats most boundaries as shared (on one sample book only 1 of 292 entries has y exactly 0; many are 54-72 pt, just a top margin). This leaves out no text but gives sections an extra trailing page of overlap. The cutoff is a single constant that can be raised (for example to 15% of the page height) if the overlap is a problem.
- Known limit: the TOC cannot tell us when a section continues past its last subsection (for example a closing summary with no entry). That trailing text is attributed to the last section.

**`BookSection` fields:** `id`, `book_id`, `parent_id`, `title`, `level`, `start_page`, `end_page`, `position`, `source`.
- `position`: reading order within the book, so tree queries have a reliable order. Costs one more column to maintain.
- `source`: `'toc'` or `'pages'`, recording whether the section came from the embedded TOC or the fallback. Helps debugging and the UI.

**Deferred for now: PDFs without a TOC are skipped while the rest of the design is worked out (revisit after the agent parts are understood). The fallback below stays as the decided plan for when we return to it.**

**Fallback for PDFs without a TOC: the page is the unit.**
- No sections are created automatically at upload. Reading and asking work on any page or page range (`start_page`..`end_page`, the same shape as a `BookSection`), so a user can ask about page 2 or pages 2-10 directly. A single page is just a range with start = end.
- The client shows page navigation when a book has no sections, and the section sidebar when it does. A mindful user can define their own ranges.
- Tradeoff: nothing to store or keep in sync, and any range is possible; but there is no ready-made sidebar for these books, and the API needs to accept a page range alongside a section.
- Heading heuristics (regex, font size) stay out until a real need appears.

**`source` is kept, and user-made TOCs are a planned extension.**
- `source` values: `'toc'` (from the PDF) and later `'user'` (a TOC the user builds for a PDF that has none). Whether `'pages'` is still needed is open, since the fallback creates no rows.
- Finalized TOCs are immutable: a TOC read from the PDF's metadata is never updated, and a user-made TOC cannot be edited once finalized. Where the finalized state lives (on `Book` or per section) is not decided yet.
- Not part of Phase 1; only noted so the schema leaves room for it.

**The top-level section is level 1; we say "section", not "chapter".**
- Not every PDF has chapters, so all docs and code use "section". The full tree is still stored; anything that needs a top-level section (for example "scope to the current top-level section") uses the level-1 ancestor of the section or page.
- Tradeoff: simple and predictable, but level 1 is whatever the PDF author chose. In one sample book, level 1 includes Cover, Copyright, Table of Contents and Preface, so front matter counts as top-level sections. Pages before the first level-1 entry belong to no top-level section. Because boundary pages can be shared (see `end_page` above), a page can fall in two top-level sections; which one wins for "current section" is not decided.

**Text storage: the PDF file is kept and read on demand; no text in the database.**
- The uploaded file is stored in S3 (during development it is saved to local `uploads/`; the move to S3 comes later, see TIMELINE.md), then fetched and loaded with PyMuPDF to read a page or range when needed.
- Storage sits behind a small interface (save, read/open, delete) so switching from local disk to S3 changes one place, not the routes. Decided, not implemented yet.
- Tradeoff: no duplicated data and a smaller database; but every read needs the file, so a fetch from S3 adds latency and a failure mode (a local cache of recently used files could help), and `Book.file_path` would hold an S3 key instead of a local path. Opening the PDF is cheap for PyMuPDF. If chunks go into a vector store later, they carry their own text.

### Under discussion (later phases)

- **RAG over the whole book vs. the current range as context.** The timeline is RAG-first (chunk, embed, retrieve, fall back to web); the original idea was to use the section being read as context. They can combine: the current page or section scopes or boosts retrieval. Tradeoffs: RAG handles long sections and cross-section questions but adds chromadb, sentence-transformers (torch, a heavy image) and chunking; range-as-context is simple but limited by the context window.
- **Database.** SQLite (current) is simple for a local single-user tool; Postgres (timeline) suits per-user progress tracking and a hosted deploy where the disk is ephemeral. Either way, schema changes need migrations (Alembic) rather than `create_all`.
- **Users and auth.** The timeline tracks reading progress per user; that implies a users table and auth, which the plan does not yet cover.
- **Embeddings.** Local sentence-transformers is free but heavy to deploy; a hosted embeddings API is lighter but costs money and adds a dependency.
- **Web fallback.** Planned as an automatic step when retrieval confidence is low (similarity score vs. an LLM check). Open: how to measure confidence, and whether the user can toggle it.
