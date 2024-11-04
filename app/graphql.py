from .database import criticism_collection, word_collection
from .schema import Criticism, WordCount, CountByAuthor, CountByCategory, CountByYear
from typing import List, Optional
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
		criticisms = await criticism_collection.find().to_list(length=1000)
		return [map_to_criticism(criticism) for criticism in criticisms]
	

	@strawberry.field
	def total_count(self) ->int:
		return criticism_collection.count_documents({})
	
	@strawberry.field
	async def word_counts(self, word: str) -> WordCount:
		result = await 	word_collection.find_one({"Word": word})
		print("result", result)
		if result is None:
			return None
		
		author_counts = [CountByAuthor(author=author["author"], count=author["count"]) for author in result.get("AuthorCounts", [])]
		year_counts = [CountByYear(year=year["year"], count=year["count"]) for year in result.get("YearCounts", [])]
		category_counts = [CountByCategory(category=category["category"], count=category["count"]) for category in result.get("CategoryCounts", [])]

		return WordCount(
			_id = result["_id"],
			Word=result["Word"],
			TotalCount=result["TotalCount"],
			AuthorCounts=author_counts,
			YearCounts=year_counts,
			CategoryCounts=category_counts
		)
				


def map_to_criticism(criticism_instance):
	return Criticism(
		id 			= str(criticism_instance["_id"]),
		author 		= criticism_instance["Author"],
		title  		= criticism_instance["Title"],
		publication = criticism_instance["Publication"],
		date 		= criticism_instance["Date"],
		place 		= criticism_instance["Place"],
		text 		= criticism_instance["Full_text"],
		url 		= criticism_instance["URL"],
		category 	= criticism_instance["Category"],
		source 		= criticism_instance["Source"],
		)
	
