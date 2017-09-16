from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, Items

engine = create_engine('sqlite:///kittycat.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

breeds = {'Persian': ['pearl', 'iphone', 'caramel mocha'],
'Maine Coon': ['double barrel', 'AK47', 'Bazooka'],
'Siamese': ['gaming computer', 'mechanical keyboard', 'nerd glasses'],
'Sphynx': ['garden hoe', 'water sprinkler', 'skinny jeans']}

cat_items = {'pearl': 'shiny pearls that cats revere',
		'iphone': 'necessity for cats who are fancy',
		'caramel mocha': 'holy water of cats',
		'double barrel': 'easy reloading shotgun',
		'AK47': 'automatic machine gun that loads sponge bullets',
		'Bazooka': 'Impact weapon that can kill many many mice',
		'gaming computer': 'necessity for nerd cats',
		'mechanical keyboard': 'easy typing for serious web dev cats',
		'nerd glasses': 'for cats who can\'t see very far',
		'garden hoe': 'needed for gardening cats',
		'water sprinkler': 'used to water the catnips',
		'skinny jeans': 'why not'}

for breed in breeds.keys():
	mycat = Catalog(name = breed)
	session.add(mycat)
	session.commit()
	for item in breeds[breed]:
		myitem = Items(name = item,
						description = cat_items[item],
						catalog = mycat
						)
		session.add(myitem)
		session.commit()
