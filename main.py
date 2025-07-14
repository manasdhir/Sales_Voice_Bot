from fastapi import FastAPI
from routes import products, websocket

app=FastAPI()
app.include_router(products.router)
app.include_router(websocket.router)