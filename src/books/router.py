from fastapi import APIRouter, HTTPException, UploadFile
from sqlmodel import select

import uuid
import pymupdf as pdf

from src.config import BASE_DIR
from src.database import SessionDep
from src.books.models import Book, BookToc

# temporary directory for uploaded files
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/books", tags=["books"])

@router.get('/')
def get_books(session: SessionDep) -> list[Book]:
  books = session.exec(select(Book)).all()
  return books

@router.get('/{book_id}/')
def get_book(book_id: int, session: SessionDep) -> Book:
  book = session.get(Book, book_id)
  if not book:
    raise HTTPException(status_code=404, detail='Book not found.')
  return book

@router.post('/')
def create_book(upload_file: UploadFile, session: SessionDep) -> Book:
  if upload_file.content_type != 'application/pdf':
    raise HTTPException(status_code=400, detail='Only PDF files are allowed.')

  book_id = uuid.uuid4()
  book_path = UPLOAD_DIR / f'{book_id}.pdf'

  try:
    with book_path.open('wb') as out:
      while chunk := upload_file.file.read(1024 * 1024):
        out.write(chunk)

    with pdf.open(book_path) as doc:
      file_name = (upload_file.filename or '').strip() or 'Untitled'
      book = Book(file_name=file_name, file_path=str(book_path))

      session.add(book)
      session.flush()

      toc = doc.get_toc()
      if toc:
        contents = [
          BookToc(title=title, page_number=page_number, page_level=page_level, book_id=book.id)
          for page_level, title, page_number in toc
        ]
        session.add_all(contents)

      session.commit()
      session.refresh(book)
  except pdf.FileDataError:
    session.rollback()
    book_path.unlink(missing_ok=True)
    raise HTTPException(status_code=400, details='The file is not a valid PDF.')
  except Exception:
    session.rollback()
    book_path.unlink(missing_ok=True)
    raise

  return book

@router.delete('/{book_id}/')
def delete_book(book_id: int, session: SessionDep):
  book = session.get(Book, book_id)

  if not book:
    raise HTTPException(status_code=404, detail='Book not found.')

  book_path = BASE_DIR / book.file_path
  session.delete(book)
  session.commit()
  book_path.unlink(missing_ok=True)

  return {'ok': True}