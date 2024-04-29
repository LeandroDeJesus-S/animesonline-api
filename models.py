from pydantic import BaseModel
from typing import Optional, Literal


class Anime(BaseModel):
    id: Optional[int]
    name: Optional[str]
    categories: Optional[str]
    year: Optional[str]
    sinopse: Optional[str]
    url: Optional[str]
    rate: Optional[float]


class Animes(BaseModel):
    animes: list[Anime]


class Episode(BaseModel):
    id: Optional[int]
    anime_id: Optional[int]
    number: Optional[int]
    date: Optional[str]
    season: Optional[int]
    url: Optional[str]


class Episodes(BaseModel):
    episodes: list[Episode]


class Season(BaseModel):
    season: int
    episodes: int


class Seasons(BaseModel):
    seasons: list[Season]


class SeasonEpisodes(BaseModel):
    season: int
    episodes: list[Episode]


class JsonResponseMessage(BaseModel):
    status_code: int
    message_type: Literal['info', 'error', 'success']
    message: str
