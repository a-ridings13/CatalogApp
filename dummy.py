from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Category, Category_Item, User

engine = create_engine('postgresql+psycopg2:///catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()


category1 = Category(user_id=1, name="Snowboarding")

session.add(category1)
session.commit()

item1 = Category_Item(user_id=1, name="xs3000", description="Modern day technology meets snowboarding,\
                                                shreds the powder like a hover board.",
                      category=category1)

session.add(item1)
session.commit()

item2 = Category_Item(user_id=1, name="Helmet", description="Protect your brain bucket with this SNELL approved helmet.",
                      category=category1)

session.add(item2)
session.commit()

category2 = Category(user_id=1, name="Rock Climbing")

session.add(category2)
session.commit()

item1 = Category_Item(user_id=1, name="Momentum Harness", description="Lightweight and breathable without compromising\
                                                           security, comfort, and durability!",
                      category=category2)

session.add(item1)
session.commit()

item2 = Category_Item(user_id=1, name="Vapor X Climbing Shoes", description="Comfortable yet durable climbing shoes, that \
                                                                 place less tension on the Achilles",
                      category=category2)

session.add(item2)
session.commit()

category3 = Category(user_id=1, name="Kayaking")

session.add(category3)
session.commit()

item1 = Category_Item(user_id=1, name="Kayak", description="Banana yellow, streamlined for all day paddling the rapids.",
                      category=category3)

session.add(item1)
session.commit()

item2 = Category_Item(user_id=1, name="Life Vest", description="Reflective buoyant PFD that's coast guard approved.",
                      category=category3)

session.add(item2)
session.commit()

category4 = Category(user_id=1, name="SCUBA Diving")

session.add(category4)
session.commit()

item1 = Category_Item(user_id=1, name="Mask", description="Black mask with comfortable silicone strap and seal.",
                      category=category4)

session.add(item1)
session.commit()

item2 =  Category_Item(user_id=1, name="BCD", description="Buoyancy Control Device designed for you to perfect neutral buoyancy.",
                                               category=category4)

session.add(item2)
session.commit()

print("added items!")