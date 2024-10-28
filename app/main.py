from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from strawberry.asgi import GraphQL
from .graphql import Query
import strawberry

app = FastAPI()

origins = [
	"http://localhost",

]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

schema = strawberry.Schema(query=Query)
app.mount("/graphql", GraphQL(schema, debug=True))

@app.get("/")
def home():
	return {"Hello world..."}


