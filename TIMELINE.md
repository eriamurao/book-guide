# Book Guide Build Plan

Check boxes show progress. Phases after 0 are still to be added from the original timeline.
Related: `OPEN_DECISIONS.md` (design questions and known bugs).

## Phase 0 — Setup (½ day)

- [x] Python 3.11+ and a virtual environment (Python 3.12, uv-managed `.venv`)
- [ ] Install core dependencies
  - [x] fastapi (installed as `fastapi[standard]`, which includes uvicorn)
  - [x] uvicorn (via `fastapi[standard]`)
  - [x] pymupdf
  - [ ] chromadb (pending open decision #2: RAG vs range-as-context)
  - [ ] sentence-transformers (same; pulls in torch, heavy for Docker)
  - [ ] anthropic
  - [ ] python-dotenv
  - [ ] pytest
- [ ] API keys in `.env`
  - [x] Anthropic API key (`ANTHROPIC_API_KEY` present)
  - [ ] Tavily API key (only if using it for web fallback)
  - [ ] `.env` untracked from git and ignored, `.env.example` added (see known bugs)
- [x] Bare FastAPI "hello world" runs
  - Command is `uv run fastapi dev src/main.py` (src layout), not `uvicorn main:app --reload`

## Phase 1 — PDF Ingestion (1–2 days)

Goal: upload a PDF, get it split into sections.

- [ ] Upload endpoint accepts a PDF file
  - Exists as `POST /books/` (timeline says `POST /books/upload`); currently broken, see known bugs in `OPEN_DECISIONS.md`
- [x] Use PyMuPDF to open the PDF and call `doc.get_toc()` (called in `create_book`)
- [ ] Keep the uploaded PDF and read page text on demand with PyMuPDF; no text in the database (decided, see README)
  - Files go to local `uploads/` while developing; moving storage to S3 is planned for later (Phase 7 deploy, or earlier if needed)
- [ ] Map TOC entries to page ranges (`start_page`, `end_page`) and split into section-level text blocks
  - `end_page` is never computed yet; `parent_id` never set
- [ ] (Deferred: PDFs without a TOC are skipped for now; revisit after the agent parts are understood) Fallback when no embedded TOC exists: no sections auto-created; reading and asking work on any page or page range (decided, see README)
  - Heading heuristics deferred until a real need appears
  - User-made TOCs (`source = 'user'`, immutable once finalized) are a later extension
- [ ] Store book metadata (file name, sections, page ranges) in the database
  - Models exist (`Book`, `BookToc`) but use SQLite, not Postgres as the timeline says; decide whether to switch (open decision #8)
  - `Book` has no `title` field yet, only `file_name`
- [ ] Checkpoint: upload a PDF and get back clean JSON of `{section_title, start_page, end_page, text}`

## Phase 2 — Chunking + Embeddings + Vector Store (1–2 days)

- [ ] Split each section's text into ~500–1000 token chunks with langchain-text-splitters (recursive splitter)
- [ ] Embed each chunk with sentence-transformers (free, local; swap to Voyage/OpenAI later if quality needs it)
- [ ] Store chunks + embeddings in ChromaDB with metadata: `book_id`, section, page range
- [ ] Retrieval function: query -> top-k similar chunks, scoped to `book_id` (optionally current section)
- [ ] Checkpoint: given a hardcoded question, retrieve relevant chunks from a specific book and print them

## Phase 3 — Core Q&A Endpoint, No Fallback Yet (1–2 days)

- [ ] `POST /ask` takes `book_id`, `query`, `current_page`
- [ ] Retrieve top chunks, build a prompt with them as context, call Claude via the SDK
- [ ] Return the answer plus the chunks/pages it came from (citations)
- [ ] Plain synchronous call first (correctness before streaming)
- [ ] Checkpoint: ask a real question about an uploaded book and get a grounded answer with citations

## Phase 4 — The Agentic Piece: Confidence Check + Web Fallback (2–3 days)

The heart of the "agent" part of the project.

- [ ] After retrieval, decide whether the chunks answer the question (ask the model, or check similarity scores)
- [ ] If confidence is low, call Tavily (or chosen search tool), feed results into a second prompt, generate the answer clearly flagged as outside the book
- [ ] Return `used_web_fallback: true/false` in the response
- [ ] Model the flow with Pydantic models (`RetrievedChunk`, `AnswerResponse`)
- [ ] Checkpoint: ask something the book doesn't cover, watch it fall back to web search and say so honestly

## Phase 5 — Make It Async + Streaming (1–2 days)

- [ ] Convert routes to `async def`, use `AsyncAnthropic`
- [ ] `StreamingResponse` so answers stream token-by-token
- [ ] `asyncio.gather()` if running retrieval + fallback confidence check concurrently
- [ ] Timeouts + retry logic (tenacity) around every external call
- [ ] Checkpoint: answers stream in visibly; a slow/failed API call degrades gracefully instead of hanging or crashing

## Phase 6 — Reading UI (3–5 days, can run in parallel with backend work)

- [ ] React frontend: PDF viewer/reader pane + section navigation sidebar
- [ ] Chat panel scoped to current page/section; pass `current_page` with every question
- [ ] Show citations (page/section) and a visible badge when web fallback was used
- [ ] Track reading progress per user in Postgres

## Phase 7 — Polish for Portfolio (2–3 days)

- [ ] README with architecture diagram (ingestion -> retrieval -> confidence check -> fallback -> answer)
- [ ] Short demo video or GIF
- [ ] Deploy (Render/Railway for backend, Vercel for frontend)
- [ ] Move uploaded-PDF storage from local `uploads/` to S3 (`Book.file_path` becomes an S3 key; add boto3 and bucket config)
- [ ] Write-up of design decisions (async, RAG-first-then-fallback)
