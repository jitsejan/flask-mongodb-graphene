""" verify.py """
from database import client
from models import Powerup


for powerup in Powerup.objects:
    print(powerup.name)
