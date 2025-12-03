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
class CountByArtist:
	artist: Optional[str]
	count: float

@strawberry.type
class CountByYear:
	year: Optional[int]
	count: float

@strawberry.type
class CountByCategory:
	category:Optional[str]
	count: float

@strawberry.type
class CountByConcept:
	concept:Optional[str]
	count: float
@strawberry.type
class CountBySentiment:
	sentiment:Optional[str]
	count: float

@strawberry.type
class WordCount:
	_id: str
	Word: str
	TotalCount: int
	WordConcept:list[str]
	ArtistCounts: list[CountByArtist]
	ConceptCounts: list[CountByConcept]
	YearCounts: list[CountByYear]
	CategoryCounts: list[CountByCategory]
	SentimentCounts: list[CountBySentiment]