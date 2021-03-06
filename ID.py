#
#   File : ID.py
#   
#   Code written by : Johann Heches
#
#   Description : Manage related functionalities to ID buffer reading/writing.
#   


import math

import Muscles
import Sensors
import Avatar

NONE = 0
LIMB = 1
MUSCLE = 2
SENSOR = 3
ZOI = 4

overGuiId = 0

"""
    Gives a unique ID to each entity from the list input.
"""
def setId(list):
    id = 0
    for entity in list:
        for part in entity:
            id += 1
            part.id = id

"""
    Converts an ID to it's corresponding color shade. Used when rendering entities on the ID buffer.
"""
def id2color(ID):
    r = math.floor(ID/math.pow(2,16))
    g = math.floor((ID%math.pow(2,16))/math.pow(2,8))
    b = ID%math.pow(2,8)
    return [r,g,b]

"""
    Converts a color shade to it's corresponding ID. Used when reading the ID buffer color at cursor location.
"""
def color2id(r,g,b):
    return int(r*math.pow(2,16) + g*math.pow(2,8) + b)

"""
    Determinate the type of the entity from it's ID.
"""
def idCategory(ID):
    if Avatar.virtuMan.limbs != [] and\
        ID >= Avatar.virtuMan.limbs[0].id and\
        ID <= Avatar.virtuMan.limbs[len(Avatar.virtuMan.limbs)-1].id:
            return LIMB
    if Avatar.virtuMan.muscles != [] and\
        ID >= Avatar.virtuMan.muscles[0].id and\
        ID <= Avatar.virtuMan.muscles[len(Avatar.virtuMan.muscles)-1].id:
            return MUSCLE
    if Sensors.virtuSens != [] and\
        ID >= Sensors.virtuSens[0].id and\
        ID <= Sensors.virtuSens[len(Sensors.virtuSens)-1].id:
            return SENSOR
    if Sensors.zoiSens != [] and\
        ID >= Sensors.zoiSens[0].id and\
        ID <= Sensors.zoiSens[len(Sensors.zoiSens)-1].id:
            return ZOI
    return NONE

"""
    Determinate the ID of the first entity from the desired type.
"""
def offsetId(type):
    if type == LIMB:
        return Avatar.virtuMan.limbs[0].id
    if type == MUSCLE:
        return Avatar.virtuMan.muscles[0].id
    if type == SENSOR:
        return Sensors.virtuSens[0].id
    if type == ZOI:
        return Sensors.zoiSens[0].id