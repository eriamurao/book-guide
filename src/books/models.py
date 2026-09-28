from sqlmodel import Field, SQLModel

class Book(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  file_name: str
  file_path: str
