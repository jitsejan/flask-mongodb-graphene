import json
from jsonpath import jsonpath
from mongoengine import connect

from models import Enemy, Level, Game, Powerup

connect('graphene-mongo-example', host='localhost', alias='default')

def init_db():
    
    with open("smb.json", "r") as file:
        data = json.loads(file.read())
    game = Game(data[0].get('table_data').get('Game'))    
    game.save()
    for row in data:
        enemies = []
        for elem in row['enemies']:
            enemy = Enemy(name=elem['name'])
            enemy.save()
            enemies.append(enemy)

        powerups = []
        for elem in row['statistics']:
            powerup = Powerup(name=elem['name'])
            powerup.save()
            powerups.append(powerup)

        level = Level(
            description = row.get('description'),
            name = jsonpath(row, 'table_data.World-Level')[0],
            world = jsonpath(row, 'table_data.World')[0],
            time_limit = jsonpath(row, 'table_data.Time limit')[0].split(' ')[0],
            boss = row.get('table_data').get('Boss'),
            enemies = enemies,
            game = game,
            powerups = powerups)

        level.save()