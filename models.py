from pydantic import BaseModel, ValidationError, validator, Field
from typing import Optional, Literal
import datetime


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

    @validator('date', pre=True, always=True)
    def parse_date(cls, value):
        if isinstance(value, datetime.date|datetime.datetime):
            try:
                return datetime.datetime.strftime(value, "%Y-%m-%d")
            except ValueError as e:
                raise ValidationError("Invalid date format, should be YYYY-MM-DD") from e
        
        return value

    @validator('season', pre=True, always=True)
    def parse_season(cls, value):
        if not isinstance(value, int):
            try:
                return int(value)
            except ValueError as e:
                raise ValidationError(f"{value} cannot be an valid integer") from e
        
        return value

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


class Headers(BaseModel):
    accept: str = 'application/json'
    Content_Type: str = Field(default='application/json', alias='Content-Type')
    X_Access_Token: str = Field(alias='X-Access-Token')

    class Config:
        allow_population_by_field_name = True
