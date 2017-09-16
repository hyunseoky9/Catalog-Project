import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
	'''
	This table contains all the user info.
	Each row is a user with name, email, picture,
	and id information
	'''
	__tablename__ = 'users'
	name = Column(
		String(80),
		nullable = False)
	id = Column(
		Integer,
		nullable = False,
		primary_key = True)
	email = Column(
		String(80),
		nullable = False)
	picture = Column(String(400))

class Catalog(Base):
	'''
	This table contains all the category info.
	Each row has the name and id of the category,
	and the user_id of a user who made the category.
	'''
	__tablename__ = 'catalog'
	name = Column(
		String(80),
		nullable = False)
	id = Column(
		Integer,
		nullable = False,
		primary_key = True)
	user_id = Column(
		Integer,
		ForeignKey('users.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return{
			'name' : self.name,
			'id' : self.id,
		}

class Items(Base):
	'''
	This table contains all the info for the items 
	that a category has. Each row is the item's name,
	description, id, catalog id that the item is under,
	and user id the item is made by.
	'''
	__tablename__ = 'items'
	name = Column(
		String(80),
		nullable = False)
	id = Column(
		Integer,
		primary_key = True)
	description = Column(
		String(500),
		nullable = False)
	catalog_id = Column(
		Integer, 
		ForeignKey('catalog.id'))
	catalog = relationship(Catalog)
	user_id = Column(
		Integer,
		ForeignKey('users.id'))
	user = relationship(User)

	@property
	def serialize(self):
		return{
			'description' : self.description,
			'id' : self.id,
			'catalog_id' : self.catalog_id,
			'name' : self.name,
		}


engine = create_engine('sqlite:///kittycat.db')
Base.metadata.create_all(engine)
