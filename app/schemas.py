from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class MarketplaceBase(BaseModel):
    name: str
    website_url: Optional[str] = None

class MarketplaceCreate(MarketplaceBase):
    pass

class MarketplaceResponse(MarketplaceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class PriceHistoryCreate(BaseModel):
    recorded_price: float

class PriceHistoryResponse(BaseModel):
    id: int
    recorded_price: float
    recorded_at: datetime
    gadget_id: int

    model_config = ConfigDict(from_attributes=True)

class GadgetBase(BaseModel):
    title: str
    brand: str
    current_price: float
    marketplace_id: int

class GadgetCreate(GadgetBase):
    pass

class GadgetUpdate(BaseModel):
    title: str
    brand: str
    current_price: float
    marketplace_id: int

class GadgetPartialUpdate(BaseModel):
    current_price: Optional[float] = None

class GadgetResponse(GadgetBase):
    id: int
    store: Optional[MarketplaceResponse] = None

    model_config = ConfigDict(from_attributes=True)