from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from strawberry.asgi import GraphQL
from .graphql import Query
import strawberry

app = FastAPI()

origins = [
	"http://localhost.tiangolo.com",
	"https://localhost.tiangolo.com",
	"http://localhost",
	"http://localhost/api/graphql",
	"http://localhost/graphql",
	"http://localhost:5173",
	"http://localhost:8000",
	"http://localhost:8000/graphql/"
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

schema = strawberry.Schema(query=Query)
app.mount("/api/graphql", GraphQL(schema, debug=True))

@app.get("/")
def home():
	return {"Hello world..."}


