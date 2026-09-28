from fastapi import FastAPI

from src.books.router import router as books_router

from src.database import create_db_and_tables

app = FastAPI()
app.include_router(books_router)

@app.on_event("startup")
def on_startup():
  create_db_and_tables()
