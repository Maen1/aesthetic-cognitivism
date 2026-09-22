from typing import Optional, List
import strawberry


@strawberry.type
class ArtistPercentage:
    artist: str
    percentage: float


@strawberry.type
class ConceptSnippet:
    concept: str
    snippets: List[str]


@strawberry.type
class Criticism:
    id: str
    author: Optional[str] = None
    title: Optional[str] = None
    publication: Optional[str] = None
    date: Optional[str] = None
    date_epoch: Optional[float] = None
    year: Optional[int] = None
    place: Optional[str] = None
    text: Optional[str] = None
    full_text: Optional[str] = None
    extracted_text: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None
    artist_percentages: List[ArtistPercentage] = strawberry.field(default_factory=list)
    found_concepts: List[str] = strawberry.field(default_factory=list)
    concept_snippets: List[ConceptSnippet] = strawberry.field(default_factory=list)


@strawberry.type
class CriticismSearchResult:
    items: List[Criticism]
    total: int
    page: int
    page_size: int
    total_pages: int


@strawberry.type
class FilterMetadata:
    categories: List[str]
    sentiments: List[str]
    total_criticisms: int


@strawberry.type
class CountByArtist:
    artist: Optional[str]
    count: float
    percentage: Optional[float] = None


@strawberry.type
class CountByYear:
    year: Optional[int]
    count: float
    normalized_count: Optional[float] = None
    total_records: Optional[int] = None


@strawberry.type
class CountByCategory:
    category: Optional[str]
    count: float
    raw_count: Optional[float] = None
    normalized_count: Optional[float] = None
    total_records: Optional[int] = None


@strawberry.type
class CountByConcept:
    concept: Optional[str]
    count: float


@strawberry.type
class CountBySentiment:
    sentiment: Optional[str]
    count: float
    raw_count: Optional[float] = None
    normalized_count: Optional[float] = None
    total_records: Optional[int] = None


@strawberry.type
class SnippetsByArtist:
    artist: Optional[str]
    snippets: List[str]


@strawberry.type
class WordCount:
    _id: str
    Word: str
    TotalCount: int
    WordConcept: List[str] = strawberry.field(default_factory=list)
    ArtistCounts: List[CountByArtist] = strawberry.field(default_factory=list)
    ArtistSnippets: List[SnippetsByArtist] = strawberry.field(default_factory=list)
    ConceptCounts: List[CountByConcept] = strawberry.field(default_factory=list)
    YearCounts: List[CountByYear] = strawberry.field(default_factory=list)
    CategoryCounts: List[CountByCategory] = strawberry.field(default_factory=list)
    SentimentCounts: List[CountBySentiment] = strawberry.field(default_factory=list)
    ConceptSnippets: List[str] = strawberry.field(default_factory=list)