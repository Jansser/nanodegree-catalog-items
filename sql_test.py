from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database import Base, Category, Item, User

engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

users = session.query(User).all()

for user in users:
    print(user.id)
    print(user.name)