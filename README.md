# GraphQL with Flask and MongoDB

In this project I will add data to a MongoDB database and make it accessible using GraphQL. 

## Prerequisites

- **Python**

  For this project I will be using Python 3.7 and `pipenv` as my virtual environment. 

- **MongoDB**

  Install MongoDB on your machine or VPS, or use a *free* [hosted](https://www.mongodb.com/cloud/atlas/lp/general/try?utm_source=compass&utm_medium=product) cluster. 

  On [Mac](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/), simply use `brew` to install the database. 
  
  ```bash
  ❯ brew tap mongodb/brew
  ❯ brew install mongodb-community@4.2
  ```

  I went with Atlas and tried one of the free clusters they offer.

   ![image-20200510214801320](images/fmg_choose_cluster.png)

  After selecting the region and the name, simply click on create and wait for the cluster to be ready.

  ![image-20200510215036769](images/fmg_cluster_being_created.PNG)

  3 minutes later the cluster will be ready.

  ![image-20200510215036769](images/fmg_show_cluster.PNG)

  Go to *Security* -> *Database Access* and create a new Database User and give Admin or Read and Write access to the database. As an optional safety guard it is smart to enable the IP whitelist and add your own IP to the list to make sure no other IPs can access your database.

  Finally go back to the *Clusters* overview and click on **Connect**. Choose the appropiate connection mechanism for your application. In my case this will be with Python 3.7. This should give you enough information to get started with MongoDB!

  ![image-20200510215729403](images/fmg_connect_cluster.png)

- [Optional] **MongoDB Compass**

  To visualize MongoDB [download](https://www.mongodb.com/download-center/compass) from their website. Use the connection string from the previous step if you want to connect to the hosted cluster directly.

  ![image-20200510215915875](images/fmg_compass_new.png)

  Once you have connected to the database the page will show your cluster, the hosts and the available data. Since we have not added anything yet it will show the default `admin` and `local` databases.

  ![image-20200510220012656](images/fmg_compass_databases.png)

## Creating the dataset

As a dataset I will be using information from https://www.mariowiki.com/. More specifcally I will be crawling data from Super Mario 1 levels from https://www.mariowiki.com/Category:Super_Mario_Bros._Levels. Each page has a table containing the **Enemies** and the **Level statistics**.

<img src="images/enemies.png" alt="enemies" style="zoom:50%;" />

<img src="images/stats.png" alt="image-20200510220901041" style="zoom:50%;" />

I will just show the reduced version here, but the whole [script](https://github.com/jitsejan/flask-mongodb-graphene/blob/master/crawl.py) is availabe in my Github repo. The script will run through the links on the website and retrieves meta data, the description, enemies and the statistics. The files are stored in a JSON file.

```python
def get_all_tables():
    """ Retrieve all the tables """
    tree = get_lxml_tree_from_url(SMB_LEVEL_URL)
    for elem in tree.cssselect('#mw-pages a'):
        url = f"{BASE_URL}{elem.get('href')}"
        print(f"Crawling data for `{url}`")
        if 'Minus' not in url:
            subtree = get_lxml_tree_from_url(url)
            yield {
                'table_data': _get_table_data(subtree),
                'description': _get_description(subtree),
                'enemies': _get_enemies(subtree),
                'statistics': _get_level_statistics(subtree),
            }

def main():
    """ Main function """
    df = pd.DataFrame.from_dict(get_all_tables())
    print(f"Found {len(df)} results")
    df.to_json('smb.json', orient='records')

if __name__ == "__main__":
    main()
```

The JSON for one item will look like the following:

```json
{
    "description": "World 1-1 is the first level of World 1 in Super Mario Bros., and the first level overall in said game; thus, it is the first level in general of the entire Super Mario series. The first screen of the level is also the game's title screen when starting it up. It contains the basics of the Super Mario Bros. game, getting the player ready for the journey ahead. The level consists of Magic Mushrooms, standard enemies such as Little Goombas and Koopa Troopas, a lot of coins, a hidden secret bonus area that allows the player to skip most of the level, Fire Flowers, pits, and a flagpole at the end. According to Shigeru Miyamoto, World 1-1 was one of the later levels created, due to the \"fun\" courses created first being more suited for late game, where players were more familiar with how Super Mario Bros. works.",
    "enemies": [
        {
            "name": "Little Goomba",
            "amount": "16"
        },
        {
            "name": "Green Koopa Troopa",
            "amount": "1"
        }
    ],
    "statistics": [
        {
            "name": "Coin",
            "amount": 39
        },
        {
            "name": "Magic Mushroom",
            "amount": 3
        },
        {
            "name": "Fire Flower",
            "amount": 3
        },
        {
            "name": "Starman",
            "amount": 1
        },
        {
            "name": "1 up Mushroom",
            "amount": 1
        }
    ],
    "table_data": {
        "World-Level": "World 1-1",
        "World": "World 1",
        "Game": "Super Mario Bros.",
        "Time limit": "400 seconds"
    }
}
```

## Storing the dataset

### Creating the schemas

In the previous step I have stored the result of the crawler to `smb.json`. To store the data in MongoDB I need to define the schema for the different tables. This is done in [models.py](https://github.com/jitsejan/flask-mongodb-graphene/blob/master/models.py) using `mongoengine` as shown below. I want to store the following four tables.

- Games
- Powerups
- Enemies
- Levels

The first collection`Game` only has a *name*, `Powerup` and `Enemy` have a *name* and *amount* and the `Level` collection will have more fields. A *Level* references a *Game* document, has a list of enemies and powerups, but also information on the time limit, boss, world and a description.

```python
""" models.py """
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (
    DateTimeField,
    ListField,
    ReferenceField,
    StringField,
    IntField,
)


class Game(Document):

    meta = {"collection": "game"}
    name = StringField()


class Powerup(Document):

    meta = {"collection": "powerup"}
    name = StringField()
    amount = IntField()


class Enemy(Document):

    meta = {"collection": "enemy"}
    name = StringField()
    amount = IntField()


class Level(Document):

    meta = {"collection": "level"}
    game = ReferenceField(Game)
    name = StringField()
    description = StringField()
    world = StringField()
    time_limit = IntField()
    boss = StringField()
    enemies = ListField(ReferenceField(Enemy))
    powerups = ListField(ReferenceField(Powerup))

```

### Loading the data into MongoDB

Now the schemas for the documents has been created, I can load the data into the MongoDB cluster that I have created before. I open the JSON file and iterate through the data. Note that I have used different methods to get data from the JSON object. One way is to use multiple `get`s to get a nest field.

```python
game = Game(name=data[0].get('table_data').get('Game'))
```

A more readable way is to use `jsonpath` like I did here, but it requires an extra import.

```python
name = jsonpath(row, 'table_data.World-Level')[0]
```

The final script to load the data is `database.py`. Since I am doing this project as a proof of concept I will always wipe the database first before adding new data.

```python
""" database.py """
import json
from jsonpath import jsonpath
from mongoengine import connect
import os

from models import Enemy, Level, Game, Powerup

DATABASE = "flask-mongodb-graphene"
PASSWORD = os.environ.get("MONGODB_PASSWORD")

client = connect(
    DATABASE,
    host=f"mongodb+srv://mongograph:{PASSWORD}@clusterjj-gazky.mongodb.net/?ssl=true&ssl_cert_reqs=CERT_NONE",
    alias="default",
)
client.drop_database(DATABASE)


def init_db():

    with open("smb.json", "r") as file:
        data = json.loads(file.read())
    game = Game(name=data[0].get("table_data").get("Game"))
    game.save()

    for row in data:
        enemies = []
        for elem in row["enemies"]:
            amount = elem["amount"] if isinstance(elem["amount"], int) else 1
            enemy = Enemy(name=elem["name"], amount=amount)
            enemy.save()
            enemies.append(enemy)

        powerups = []
        for elem in row["statistics"]:
            powerup = Powerup(name=elem["name"], amount=elem["amount"])
            powerup.save()
            powerups.append(powerup)

        level = Level(
            description=row.get("description"),
            name=jsonpath(row, "table_data.World-Level")[0],
            world=jsonpath(row, "table_data.World")[0],
            time_limit=jsonpath(row, "table_data.Time limit")[0].split(" ")[0],
            boss=row.get("table_data").get("Boss"),
            enemies=enemies,
            game=game,
            powerups=powerups,
        )

        level.save()


init_db()

```

To populate the database run the script:

```bash
❯ python database.py
```

## Verifying the dataset

### Option 1. Verifying it using the website

![image-20200515030104694](/Users/jitsejan/Library/Application Support/typora-user-images/image-20200515030104694.png)

### Option 2. Verify using MongoDB Compass

#### Database overview

![image-20200510230858416](/Users/jitsejan/Library/Application Support/typora-user-images/image-20200510230858416.png)

#### Collection overview

![image-20200510231351275](/Users/jitsejan/Library/Application Support/typora-user-images/image-20200510231351275.png)

#### Detailed collection view

![image-20200510231508583](/Users/jitsejan/Library/Application Support/typora-user-images/image-20200510231508583.png)

### Option 3. Using Python

```python
""" verify.py """
from database import client
from models import Powerup


for powerup in Powerup.objects:
    print(powerup.name)

# OUTPUT
# Coin
# Magic Mushroom
# Fire Flower
# Starman
# 1 up Mushroom
# Coin
# Magic Mushroom
# Fire Flower
# Starman
# 1 up Mushroom
# Coin
# Magic Mushroom
# Fire Flower
```

<img src="/Users/jitsejan/Library/Application Support/typora-user-images/image-20200515024948495.png" alt="image-20200515024948495" style="zoom:50%;" />

## Setting up GraphQL

To make the data accessible with GraphQL I need to convert models from the previous step to a GraphQL schema. Firstly, I need the `graphene` dependencies to create the schema specifically for a MongoDB connection. After importing the dependencies I import all the models from my `models.py`. Now each model has to be setup as a node in the GraphQL Schema where `Query` is the top of the graph. In the `Query` class I have defined three different queries:

- Get all levels
- Get all enemies
- Get all powerups

```python
""" schema.py """
import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineConnectionField, MongoengineObjectType

from models import Game as GameModel
from models import Powerup as PowerupModel
from models import Enemy as EnemyModel
from models import Level as LevelModel


class Game(MongoengineObjectType):
    class Meta:
        description = "Game"
        model = GameModel
        interfaces = (Node,)


class Powerup(MongoengineObjectType):
    class Meta:
        description = "Power-ups"
        model = PowerupModel
        interfaces = (Node,)


class Enemy(MongoengineObjectType):
    class Meta:
        description = "Enemies"
        model = EnemyModel
        interfaces = (Node,)


class Level(MongoengineObjectType):
    class Meta:
        description = "Levels"
        model = LevelModel
        interfaces = (Node,)


class Query(graphene.ObjectType):
    node = Node.Field()

    all_levels = MongoengineConnectionField(Level)
    all_enemies = MongoengineConnectionField(Enemy)
    all_powerups = MongoengineConnectionField(Powerup)


schema = graphene.Schema(query=Query, types=[Powerup, Level, Enemy, Game])

```

To start the server now the schema is defined we need to create the application. Flask is used as web application with one path (rule) to the GraphQL endpoint. I connect to the MongoDB database and set the database. The server is started on port 5002.

```
""" app.py """
from flask import Flask
from flask_graphql import GraphQLView
from mongoengine import connect
import os

from schema import schema

DATABASE = 'flask-mongodb-graphene'
PASSWORD = os.environ.get("MONGODB_PASSWORD")

client = connect(DATABASE, host=f'mongodb+srv://mongograph:{PASSWORD}@clusterjj-gazky.mongodb.net/?ssl=true&ssl_cert_reqs=CERT_NONE', alias='default')

app = Flask(__name__)
app.debug = True

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(port=5002)
```

Go to your terminal and run the webapp:

```bash
❯ python app.py
```

## Verifying GraphQL

### Option 1. Verify using the Flask version of GraphiQL

Go to `localhost:5002/graphql` and run the `allPowerups` query to get back the names of all the power-ups. 

![image-20200515022601294](/Users/jitsejan/Library/Application Support/typora-user-images/image-20200515022601294.png)

### Option 2. Verify using GraphiQL application

Using the standalone application [GraphiQL](https://www.electronjs.org/apps/graphiql) it is easy to test the GraphQL endpoint. Using the `allEnemies` query defined in `schema.py` we get back all the enemies and their amounts.

![image-20200515024714801](/Users/jitsejan/Library/Application Support/typora-user-images/image-20200515024714801.png)

### Option 3. Using Postman

I have used [Postman](https://www.postman.com) for a long time for testing my REST APIs and fortunately it also supports GraphQL APIs. 

![image-20200515022846519](/Users/jitsejan/Library/Application Support/typora-user-images/image-20200515022846519.png)

And that should do it. In an