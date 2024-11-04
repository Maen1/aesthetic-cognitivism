from typing import Optional
import strawberry

@strawberry.type
class Criticism:
	id: str
	author 		: Optional[str]
	title  		: Optional[str]
	publication : Optional[str]
	date 		: Optional[str]
	place 		: Optional[str]
	text 		: Optional[str]
	url 		: Optional[str]
	category 	: Optional[str]
	source		: Optional[str]
	



@strawberry.type
class CountByAuthor:
	author: Optional[str]
	count: int

@strawberry.type
class CountByYear:
	year: Optional[int]
	count: int

@strawberry.type
class CountByCategory:
	category:Optional[str]
	count: int

@strawberry.type
class WordCount:
	_id: str
	Word: str
	TotalCount: int
	AuthorCounts: list[CountByAuthor]
	YearCounts: list[CountByYear]
	CategoryCounts: list[CountByCategory]