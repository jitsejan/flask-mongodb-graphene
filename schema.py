import graphene
from graphene.relay import Node
from graphene_mongo import MongoengineConnectionField, MongoengineObjectType
from models import Game as GameModel
from models import Powerup as PowerupModel
from models import Enemy as EnemyModel
from models import Level as LevelModel


class Game(MongoengineObjectType):

    class Meta:
        model = GameModel
        interfaces = (Node,)


class Powerup(MongoengineObjectType):

    class Meta:
        model = PowerupModel
        interfaces = (Node,)


class Enemy(MongoengineObjectType):

    class Meta:
        model = EnemyModel
        interfaces = (Node,)


class Level(MongoengineObjectType):

    class Meta:
        model = LevelModel
        interfaces = (Node,)


class Query(graphene.ObjectType):
    node = Node.Field()
    all_levels = MongoengineConnectionField(Level)
    all_powerups = MongoengineConnectionField(Powerup)
    powerup = graphene.Field(Powerup)


schema = graphene.Schema(query=Query, types=[Powerup, Level, Enemy, Game])
