from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class Marketplace(Base):
    __tablename__ = "marketplaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    website_url = Column(String)

    gadgets = relationship("Gadget", back_populates="store", cascade="all, delete-orphan")


class Gadget(Base):
    __tablename__ = "gadgets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    brand = Column(String, index=True)
    current_price = Column(Float)

    marketplace_id = Column(Integer, ForeignKey("marketplaces.id"))

    store = relationship("Marketplace", back_populates="gadgets")
    price_records = relationship("PriceHistory", back_populates="gadget_item", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    recorded_price = Column(Float)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    gadget_id = Column(Integer, ForeignKey("gadgets.id"))

    gadget_item = relationship("Gadget", back_populates="price_records")