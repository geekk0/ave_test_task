import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
from pydantic import BaseModel, constr

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
metadata = MetaData()

with open("test_exercise_2.txt", "r") as file:
    data = file.readlines()
    headers = data[0].strip().split(",")
    columns = [Column(header, String) for header in headers if header != 'id']

items_table = Table('items', metadata, Column('id', Integer,
                                              primary_key=True,
                                              index=True,
                                              autoincrement=True), *columns)
metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    if not db.execute(items_table.select()).fetchone():
        for line in data[1:]:  # Skip the first line with headers
            values = line.strip().split(",")
            item_data = {header: value for header, value in zip(headers, values) if header != 'id'}
            db.execute(items_table.insert().values(**item_data))
        db.commit()
    yield


app = FastAPI(lifespan=lifespan)


class ItemCreate(BaseModel):
    name: constr(min_length=1)
    email: str
    phone: str
    note: str


class Item(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    note: str


@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    result = db.execute(items_table.insert().values(name=item.name, email=item.email, phone=item.phone, note=item.note))
    db.commit()
    item_id = result.inserted_primary_key[0]
    return Item(id=item_id, name=item.name, email=item.email, phone=item.phone, note=item.note)


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    query = db.execute(items_table.select().where(items_table.c.id == item_id))
    item = query.fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(id=item.id, name=item.name, email=item.email, phone=item.phone, note=item.note)


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    query = db.execute(items_table.select().where(items_table.c.id == item_id))
    db_item = query.fetchone()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.execute(items_table.update().where(items_table.c.id == item_id).values(name=item.name, email=item.email,
                                                                              phone=item.phone, note=item.note))
    db.commit()
    return Item(id=item_id, name=item.name, email=item.email, phone=item.phone, note=item.note)


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    query = db.execute(items_table.select().where(items_table.c.id == item_id))
    db_item = query.fetchone()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.execute(items_table.delete().where(items_table.c.id == item_id))
    db.commit()
    return {"detail": "Item deleted"}
