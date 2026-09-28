# Book Guide

An AI agent that helps you read and understand PDFs — books, contracts, or anything else.

## Goal

Upload a PDF and read it chapter by chapter, or page by page, using the table of contents. Ask the agent to explain the part you are reading. That part is the retrieval context for the answer. If you want more context, the agent can also search the web.

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
