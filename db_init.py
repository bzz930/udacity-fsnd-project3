from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from db_setup import Category, Item, User, Base

engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

user1 = User(username='admin',
             email='bianzhengzhen@gmail.com',
             picture='../static/admin.jpg')
session.add(user1)
session.commit()

category1 = Category(name='Clothing', user_id=1)
session.add(category1)
session.commit()

item1 = Item(name='Down Jacket',
            description='Rugged synthetic down warmth and sustainably-minded \
            design in a puffy that insulates your everyday adventures.',
            category=category1, user_id=1)
session.add(item1)
session.commit()

item2 = Item(name='Rain Jacket',
             description='Pack light and go far with the ultimate in GORE-TEX \
             Paclite weatherproof performance.',
             category=category1, user_id=1)
session.add(item2)
session.commit()

item3 = Item(name='Full-Zip Hoodie',
             description='Low-key lounging or warming up for a workout, stay \
             cool with a blend of style and regulated comfort.',
             category=category1, user_id=1)
session.add(item3)
session.commit()

item4 = Item(name='T-Shirt',
             description="Oxygen, food, water, and a fresh Women's Burton Bel \
             Mar Raglan - life has its essentials. Keep your mind wandering at \
             all times with this everyday wardrobe necessity.",
             category=category1, user_id=1)
session.add(item4)
session.commit()

category2 = Category(name='Bags & Luggage', user_id=1)
session.add(category2)
session.commit()

item5 = Item(name='Backpack',
             description='Even a mountain man needs to phone home. Heritage \
             rucksack design with secure laptop and electronics compartments \
             plus external webbing to stash a jacket.',
             category=category2, user_id=1)
session.add(item5)
session.commit()

item6 = Item(name='Duffel Bag',
             description="Basic day trip storage that keeps foot funk a \
             private matter. Shoes to boots, plus extras...it's all got a spot.",
             category=category2, user_id=1)
session.add(item6)
session.commit()

item7 = Item(name='Board Bag',
             description='Plane, train, or automobile. Take the puzzle out of \
             packing with fully padded multiple board protection, organizer \
             pockets, and removable shoulder carry for easy hauling.',
             category=category2, user_id=1)
session.add(item7)
session.commit()

category3 = Category(name='Gear', user_id=1)
session.add(category3)
session.commit()

item8 = Item(name='Snowboard',
             description="Bad-ass with a touch of sass in an action-packed \
             board that'll have you falling in love with camber all over again.",
             category=category3, user_id=1)
session.add(item8)
session.commit()

item9 = Item(name='Helmet',
             description="Simple, skate-inspired performance for year-round, \
             on and off-snow protection.",
             category=category3, user_id=1)
session.add(item9)
session.commit()

item10 = Item(name='Goggles',
              description='Low-profile performance meets a wide field of \
              vision, plus SONAR lens technology by ZEISS for ultimate \
              contrast and clarity.',
              category=category3, user_id=1)
session.add(item10)
session.commit()

print 'added categories and items!'
