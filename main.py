from fastapi import FastAPI
from strawberry.asgi import GraphQL

from schema import schema

app = FastAPI()

@app.get("/")
async def index():
    return {"message": "FastAPI with Strawberry GraphQL"}

app.add_route("/graphql", GraphQL(schema))
app.add_websocket_route("/graphql", GraphQL(schema))