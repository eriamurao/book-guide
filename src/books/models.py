from sqlmodel import Field, SQLModel

class Book(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  file_name: str
  file_path: str

class BookToc(SQLModel, table=True):
  __tablename__ = 'book_toc'

  id: int | None = Field(default=None, primary_key=True)
  title: str
  page_number: int
  page_level: int
  book_id: int | None = Field(default=None, foreign_key='book.id')