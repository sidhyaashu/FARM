from contextlib import asynccontextmanager
from datetime import datetime
import os
import sys

from bson import ObjectId
from fastapi import FastAPI, status, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import uvicorn

from dal import ToDoDAL, ListSummary, ToDoList

COLLECTION_NAME = "todo_lists"
MONGO_URL = os.environ.get("MONGODB_URI")
if not MONGO_URL:
    raise ValueError("Environment variable MONGODB_URI is required.")

DEBUG = os.environ.get("DEBUG", "").strip().lower() in {"1", "true", "on", "yes"}

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(MONGO_URL)
    database = client.get_default_database()

    pong = await database.command("ping")
    if int(pong["ok"]) != 1:
        raise Exception("Cluster Connection is not Okay!")

    todo_lists = database.get_collection(COLLECTION_NAME)
    app.state.todo_dal = ToDoDAL(todo_lists)

    yield

    client.close()

app = FastAPI(lifespan=lifespan, debug=DEBUG)

@app.get("/api/lists", response_model=list[ListSummary])
async def get_all_lists():
    todo_dal = app.state.todo_dal
    return [i async for i in todo_dal.list_todo_lists()]

class NewList(BaseModel):
    name: str

class NewListResponse(BaseModel):
    id: str
    name: str

@app.post("/api/lists", status_code=status.HTTP_201_CREATED, response_model=NewListResponse)
async def create_todo_list(new_list: NewList):
    todo_dal = app.state.todo_dal
    return NewListResponse(
        id=await todo_dal.create_todo_list(new_list.name),
        name=new_list.name,
    )

@app.get("/api/lists/{list_id}", response_model=ToDoList)
async def get_list(list_id: str):
    todo_dal = app.state.todo_dal
    todo_list = await todo_dal.get_todo_list(list_id)
    if not todo_list:
        raise HTTPException(status_code=404, detail="List not found")
    return todo_list

@app.delete("/api/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: str):
    todo_dal = app.state.todo_dal
    deleted = await todo_dal.delete_todo_list(list_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="List not found")

class NewItem(BaseModel):
    label: str

@app.post("/api/lists/{list_id}/items/", status_code=status.HTTP_201_CREATED, response_model=ToDoList)
async def create_item(list_id: str, new_item: NewItem):
    todo_dal = app.state.todo_dal
    return await todo_dal.create_item(list_id, new_item.label)

@app.delete("/api/lists/{list_id}/items/{item_id}", response_model=ToDoList)
async def delete_item(list_id: str, item_id: str):
    todo_dal = app.state.todo_dal
    return await todo_dal.delete_item(list_id, item_id)

class ToDoUpdate(BaseModel):
    item_id: str
    checked_state: bool

@app.patch("/api/lists/{list_id}/checked_state", response_model=ToDoList)
async def set_checked_state(list_id: str, update: ToDoUpdate):
    todo_dal = app.state.todo_dal
    return await todo_dal.set_checked_state(
        list_id, update.item_id, update.checked_state
    )

class DummyResponse(BaseModel):
    id: str
    when: datetime

@app.get("/api/dummy", response_model=DummyResponse)
async def get_dummy():
    return DummyResponse(
        id=str(ObjectId()),
        when=datetime.now(),
    )

def main(argv=sys.argv[1:]):
    try:
        uvicorn.run("server:app", host="0.0.0.0", port=3001, reload=DEBUG)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
