from pydantic import BaseModel, field_validator, Field
from typing import Union, Optional, Any, ClassVar
from dateutil import parser
from .utils import extract_numeric, extract_unit, get_valid_path

### Notes: 
# if there are multiple fields in the class, override init function to take an input str and process it to extract the required fields
# if there is only one field, use field_validator to extract the required fields


class CARDINAL(BaseModel):
    """Numerals that do not fall under another type"""
    value: Any = Field(..., description="Value of cardinal numeral")
    description: ClassVar[str] = "Any cardinal numerals"

    @field_validator('value')
    @classmethod
    def get_numeric(cls,v):
        return extract_numeric(v)

class DATE(BaseModel):
    """Absolute or relative dates or periods"""
    date: str = Field(..., description="string value of date")
    description: ClassVar[str] = "Any absolute or relative dates or period in appropriate date format"

    @field_validator('date')
    @classmethod
    def check_date_format(cls, v):
        try:
            parsed_date = parser.parse(v, default=None)

            # Check specificity of the date and format accordingly
            if parsed_date.hour == 0 and parsed_date.minute == 0 and parsed_date.second == 0:
                # Date only
                return parsed_date.strftime('%Y%m%d')
            # Optionally, convert to a specific format, e.g., ISO 8601
            else:
                return parsed_date.strftime('%Y%m%dT%H')
        except ValueError:
            raise ValueError("Invalid date format")

class EVENT(BaseModel):
    """Named hurricanes, battles, wars, sports events, etc."""
    name: str = Field(..., description="Name of the event")
    description: ClassVar[str] = "Any named events"

class FAC(BaseModel):
    """Buildings, airports, highways, bridges, etc."""
    name: str = Field(..., description="Name of the facility")
    description: ClassVar[str] = "Any named facilities like buildings, airports, highways, bridges, etc."

class GPE(BaseModel):
    """Countries, cities, states"""
    name: str = Field(..., description="Name of the geographical location")
    description: ClassVar[str] = "Any named geographical locations like countries, cities, states"

class LANGUAGE(BaseModel):
    # LANGUAGE :  Any named language
    name: str = Field(..., description="Name of the language")
    description: ClassVar[str] = "Any named language"

class LAW(BaseModel):
    # LAW :  Named documents made into laws.
    name: str = Field(..., description="Name of the law")
    description: ClassVar[str] = "Any named documents made into laws"

class LOC(BaseModel):
    ## LOC :  Non-GPE locations, mountain ranges, bodies of water
    name: str = Field(..., description="Name of the location")
    description: ClassVar[str] = "Any named non-GPE locations like mountain ranges, bodies of water"

class MONEY(BaseModel):
    # MONEY :  Monetary values, including unit
    value: Union[float, int] = Field(..., gt=0,description="Value of the monetary amount")
    currency: Optional[str] = Field("USD", description="Currency of the monetary amount")
    description: ClassVar[str] = "Any monetary values, including unit (default: USD if not found.)"

    def __init__(self, input_string: str):
        numeric_part = extract_numeric(input_string)
        unit_part = extract_unit(input_string)
        super().__init__(value=numeric_part, currency=unit_part)

class NORP(BaseModel):
    # NORP :  Nationalities or religious or political groups
    name: str = Field(..., description="Name of the group")
    description: ClassVar[str] = "Any named nationalities or religious or political groups"

class ORDINAL(BaseModel):
    # ORDINAL :  "first", "second", etc.
    value: str = Field(..., description="Ordinal value")
    description: ClassVar[str] = "Any ordinal values like 'first', 'second', etc."

class ORG(BaseModel):
    # ORG :  Companies, agencies, institutions, etc.
    name: str = Field(..., description="Name of the organization")
    description: ClassVar[str] = "Any named organizations like companies, agencies, institutions, etc."

class PERCENT(BaseModel):
    # PERCENT :  Percentage, including "%"
    value: Union[float, int] = Field(..., gt=0, lt=100,description="Value of percentage")
    description: ClassVar[str] = "Any percentage values"

class PERSON(BaseModel):
    # PERSON :  People, including fictional
    name: str = Field(..., description="Name of the person")
    description: ClassVar[str] = "Any named persons, including fictional"

class PRODUCT(BaseModel):
    # PRODUCT :  Objects, vehicles, foods, etc. (not services)
    name: str = Field(..., description="Name of the product")
    description: ClassVar[str] = "Any named products like objects, vehicles, foods, etc."

class QUANTITY(BaseModel):
    # QUANTITY :  Measurements, as of weight or distance
    value: Union[float, int] = Field(...,description="Value of the quantity measurement")
    unit: Optional[str] = Field(None, description="Unit of quantity measurement")
    description: ClassVar[str] = "Any quantity measurements, as of weight or distance"

    def __init__(self, input_string: str=None, **kwargs):
        if input_string is None:
            super().__init__(**kwargs)
        else:
            numeric_part = extract_numeric(input_string)
            unit_part = extract_unit(input_string)
            super().__init__(value=numeric_part, unit=unit_part)

    
class TIME(BaseModel):
    # TIME :  Times smaller than a day
    time: str = Field(...,description="Value of time") # Assuming HH:MM:SS format
    description: ClassVar[str] = "Any time values in HH:MM:SS like format"

    @field_validator('time')
    @classmethod
    def check_time_format(cls, v):
        try:
            # Parse the string to datetime object
            parsed_time = parser.parse(v)
            # Extract the time part
            extracted_time = parsed_time.time()
            # Optionally, convert to a specific string format if needed
            return extracted_time.strftime('%H:%M:%S')
        except ValueError:
            raise ValueError("Invalid time format")

class WORK_OF_ART(BaseModel):
    # WORK_OF_ART :  Titles of books, songs, etc.
    name: str = Field(..., description="Name of the work of art")
    description: ClassVar[str] = "Any named works of art like titles of books, songs, etc."

class FilePath(BaseModel):
    path: str = Field(..., description="File or folder path")
    description: ClassVar[str] = "File or folder path"

    def __init__(self, path: str, **kwargs):
        """
        kwargs: dict-> search_root='/', use_regex=False, case_sensitive=False, max_depth=None
        """
        path = get_valid_path(path, **kwargs)
        super().__init__(path=path)

# class CustomList(BaseModel):
#     item_type: Union[str, type]
#     items: List[Any]
#     description: ClassVar[str] = f"A list of items of type {item_type}. The description of the item type is as follows: {item_type.description}"
# class CustomDict(BaseModel):
#     items: Dict[str, Any] = Field(..., description="A dictionary of key-value pairs")

# class CustomTuple(BaseModel):
#     items: Tuple[Any, ...] = Field(..., description="A tuple of items")