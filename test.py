from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name:str
    price:float
    is_offer:Union[bool,None] = None


@app.get("/")
def read_root():
    return {"Hello":"World"}


@app.get("/items/{item_id}")
def red_item(item_id:int,q:Union[str,None] = None):
    return {"Item ID":item_id,"Q":q}


@app.put("/items/{item_id}")
def update_item(item_id:int,item:Item):
    return {"Item Name":item.name,"Item ID":item_id}