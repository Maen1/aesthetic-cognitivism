from .database import criticism_collection
from .schema import Criticism
from typing import List
from bson import ObjectId
import strawberry


@strawberry.type
class Query:
	@strawberry.field
	async def criticism(self, id:str) -> Criticism:
		criticism = await(criticism_collection.find_one(ObjectId(id)))
		if criticism:
			return map_to_criticism(criticism)
		
		return ValueError(f"Criticism not found {id}")
		
	@strawberry.field
	async def criticisms(self)  -> List[Criticism]:
		criticisms = await criticism_collection.find().to_list(length=10000)
		return [map_to_criticism(criticism) for criticism in criticisms]
	



def map_to_criticism(criticism_instance):
	return Criticism(
		id 			= str(criticism_instance["_id"]),
		author 		= criticism_instance["Author"],
		title  		= criticism_instance["Title"],
		publication = criticism_instance["Publication"],
		data 		= criticism_instance["Date"],
		place 		= criticism_instance["Place"],
		text 		= criticism_instance["Full_text"],
		url 		= criticism_instance["URL"],
		category 	= criticism_instance["Category"],
		source 		= criticism_instance["Source"]
		)
	