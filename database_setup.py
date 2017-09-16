import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Catalog(Base):
	__tablename__ = 'catalog'
	name = Column(
		String(80),
		nullable = False)
	id = Column(
		Integer,
		nullable = False,
		primary_key = True)

	@property
	def serialize(self):
		return{
			'name' : self.name,
			'id' : self.id,
		}

class Items(Base):
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
