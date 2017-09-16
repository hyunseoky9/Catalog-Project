# KITTYCATALOG
## What it's all about
This repo contains all the files necessary to start up a catalog about cats.
Each cats have certain items that signed in users can give, edit, and take away.
The signed in user can also create, delete a cat, or edit it's name.
The users have to log in via google plus, and they can only edit or delete 
items or cats that they created.

## How to Use
Vagrant up has all the dependencies necessary to run this app.
Clone Udacity's repo 'fullstack-nanodegree-vm' and clone my repo in there.

Download Vagrant up and Virtual Machine. Once you have downloaded them and 
started the virtual environment by typing ```vagrant ssh``` in bash or git bash (in windows).

Type ```cd /vagrant``` and you should see the repo ```catalog```.
Once you go into this folder, type ```python database_setup.py``` and then ```python kittycat.db```.
Once the database is created and populated through those two commands, type ```python catalog.py```
to start the server, and then go to localhost:8000/ or localhost:8000/kittycat.

Enjoy!

**This project was created by Hyun Seok Yoon for the Udacity full stack web development nanodegree program**