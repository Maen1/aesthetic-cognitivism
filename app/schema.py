from typing import Optional
import strawberry

@strawberry.type
class Criticism:
	id: str
	author 		: Optional[str]
	title  		: Optional[str]
	publication : Optional[str]
	data 		: Optional[str]
	place 		: Optional[str]
	text 		: Optional[str]
	url 		: Optional[str]
	category 	: Optional[str]
	source		: Optional[str]




