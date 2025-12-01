from .database import criticism_collection, word_collection
from .schema import Criticism, WordCount, CountByArtist, CountByCategory, CountByYear, CountByConcept
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
	async def word_counts(self, words: List[str]) -> List[WordCount]:
		# Fetch the result from the database
		cursor = word_collection.find({"Word":{"$in": words}})
		results = await cursor.to_list(length=None)
		print(results)
		# Check if the result is None and handle the case
		if not results:
			return None  # Returning None will indicate no result found
		word_count_list = []
		for result in results:
			year_counts = [
				CountByYear(year=year, count=count) 
				for year, count in result.get("YearCounts", {}).items()
				]
			category_counts = [
				CountByCategory(category=category, count=count) 
				for category, count in result.get("CategoryCounts", {}).items()
				]
			artist_counts = [
				CountByArtist(artist=artist, count=count) 
				for artist, count in result.get("ArtistCounts", {}).items()
				]
			
			concept_counts = [
				CountByConcept(concept=concept, count=count) 
				for concept, count in result.get("ConceptCounts", {}).items()
				]


		# Create and return the WordCount object
			word_count_list.append(WordCount(
				_id=result.get("_id"),  
				Word=result.get("Word", ""),  
				WordConcept=result.get("WordConcept", ""),  
				TotalCount=result.get("TotalCount", 0), 
				YearCounts=year_counts,
				CategoryCounts=category_counts,
				ArtistCounts=artist_counts,
				ConceptCounts=concept_counts
			))
		return word_count_list


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
	
