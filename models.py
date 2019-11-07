from datetime import datetime
from mongoengine import Document, EmbeddedDocument
from mongoengine.fields import (
    DateTimeField, ListField, ReferenceField, StringField,
    IntField,
)

class Game(Document):
    
    meta = {'collection': 'game'}
    name = StringField()
    
class Powerup(Document):

    meta = {'collection': 'powerup'}
    name = StringField()
    
class Enemy(Document):

    meta = {'collection': 'enemy'}
    name = StringField()

class Level(Document):
    
    meta = {'collection': 'level'}
    game = ReferenceField(Game)
    name = StringField()
    description = StringField()
    world = StringField()
    time_limit = IntField()
    boss = StringField()
    enemies = ListField(ReferenceField(Enemy))
    powerups = ListField(ReferenceField(Powerup))
