"""
Populate the database with categories and items.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Category, Item, User

engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Creating a user
jaspion = User(name="Jaspion",
               email="jaspion.gmail.com",
               picture="http://modomeu.com/wp-content/"
               "uploads/2015/05/23-jaspion.jpg")
session.add(jaspion)
session.commit()

# Creating all the categories and items
soccer = Category(name="Soccer")
session.add(soccer)
session.commit()

frisbee = Category(name="Frisbee")
session.add(frisbee)
session.commit()

basketball = Category(name="Basketball")
session.add(basketball)
session.commit()

baseball = Category(name="Baseball")
session.add(baseball)
session.commit()

hockey = Category(name="Hockey")
session.add(hockey)
session.commit()

snowboarding = Category(name="Snowboarding")
session.add(snowboarding)
session.commit()

soccer_cleats = Item(name="Soccer Cleats",
                     category_id=soccer.id, user_id=jaspion.id)
session.add(soccer_cleats)
session.commit()

jersey = Item(name="Jersey", category_id=soccer.id, user_id=jaspion.id)
session.add(jersey)
session.commit()

bat = Item(name="Bat", category_id=baseball.id, user_id=jaspion.id)
session.add(bat)
session.commit()

frisbee_item = Item(name="Frisbee", category_id=frisbee.id, user_id=jaspion.id)
session.add(frisbee)
session.commit()

shinguards = Item(name="Shinguards", category_id=soccer.id, user_id=jaspion.id)
session.add(shinguards)
session.commit()

two_shinguards = Item(name="Two shinguards",
                      category_id=soccer.id, user_id=jaspion.id)
session.add(two_shinguards)
session.commit()

snowboard = Item(name="Snowboard",
                 category_id=snowboarding.id, user_id=jaspion.id)
session.add(snowboard)
session.commit()

goggles = Item(name="Goggles", category_id=snowboarding.id, user_id=jaspion.id)
session.add(goggles)
session.commit()

stick = Item(name="Stick", category_id=hockey.id, user_id=jaspion.id)
session.add(stick)
session.commit()
