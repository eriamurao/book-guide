from sqlmodel import Field, Relationship, SQLModel

class Book(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  file_name: str
  file_path: str

  toc: list['BookToc'] = Relationship(back_populates='book', cascade_delete=True)

class BookToc(SQLModel, table=True):
  __tablename__ = 'book_toc'

  id: int | None = Field(default=None, primary_key=True)
  title: str
  start_page: int
  end_page: int
  level: int

  parent_id: int | None = Field(default=None, foreign_key='book_toc.id', index=True)
  parent: 'BookToc | None' = Relationship(back_populates='children', sa_relationship_kwargs={'remote_side': 'BookToc.id'})
  children: list['BookToc'] = Relationship(back_populates='parent')
  
  book_id: int = Field(foreign_key='book.id', index=True)
  book: Book | None = Relationship(back_populates='toc')
