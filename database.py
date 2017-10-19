import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250), nullable=False)


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())
    image_filename = Column(String)
    image_url = Column(String)

    category_id = Column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="items")
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id
        }


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    items = relationship("Item", order_by=Item.id, back_populates="category")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'items': self.serialize_item
        }

    @property
    def serialize_item(self):
        return [item.serialize for item in self.items]


engine = create_engine("sqlite:///catalog.db")
Base.metadata.create_all(engine)
