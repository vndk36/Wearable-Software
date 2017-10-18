class sensors(object):
    """
        characteristics
        .x      attachment distance
        .t      attachment angle
    """
    __name__ = "sensors"
    nb__init__ = 0 # keeps track of how many creations there are


    def __init__(self, attach = "Origin", type = "Custom", coord = (0, 0), color = (1,0,0)): # add orientation sometime...
        """ constructor """
        sensors.nb__init__ += 1
        self.attach = attach
        self.type = type
        self.x = coord[0]
        self.t = coord[1]
        self.s = coord[2]
        self.h = 0.
        self.color = color

    @classmethod
    def feedback(cls,reset = False):
        """ print feedback on class calls """
        print("nb__init__ : {}".format(sensors.nb__init__))
        if reset == True:
            sensors.nb__init__ = 0
            print("reset for {} is done".format(cls.__name__))
        print("\n")
        

    def values(self):
        """ print characteristics values """
        print(self.attach, self.x, self.t)



virtuSens = ["",]
selectedSens = []

from OpenGL.GL import *
from OpenGL.GLU import *
import math
import time
import numpy as np

import Cursor
import Definitions
import Events
import Graphics
import Shaders

countID = 0
def preprocessSensor(sensor, x, y, z):
    global countID
    countID += 1
    Definitions.transform.push()

    """ sensor orientation """
    u = Definitions.vector4D.Eul2Quat(Definitions.vector4D((0, 0, 90, 0)))
    v = Definitions.vector4D.Eul2Quat(Definitions.vector4D((0, 0, 0, sensor.t)))
    s = Definitions.vector4D.Eul2Quat(Definitions.vector4D((0, 0, sensor.s-90, 0)))
    w = Definitions.vector4D.Eul2Quat(Definitions.vector4D((0, time.clock()*100, 0, 0)))
    t = Definitions.vector4D.Quat2Vec(Definitions.vector4D.QuatProd(u, Definitions.vector4D.QuatProd(v, Definitions.vector4D.QuatProd(s,w))))

    """ transformation matrix update """
    Definitions.transform.push()
    Definitions.transform.translate(sensor.x, 0, 0)

    if math.sqrt(t.x*t.x + t.y*t.y + t.z*t.z) >= 0.0001:
        """ transformation matrix update """
        Definitions.transform.rotate(t.o, t.x, t.y, t.z)

        Definitions.transform.push()
        Definitions.transform.scale(sensor.h,1,1)
        Definitions.transform.translate(0.5, 0, 0)
        
        """ store transformation in package """
        Definitions.packagePreprocess[Graphics.vboDashed] = Definitions.packagePreprocess[Graphics.vboDashed] + [[Definitions.transform.peek(), "Link", countID, sensor],]
        #Definitions.packageDashed = Definitions.packageDashed + [[Definitions.transform.peek(), sensor],]
        
        Definitions.transform.pop()
        
    """ transformation matrix update """
    Definitions.transform.translate(sensor.h, 0, 0)
    Definitions.transform.rotate(-t.o, t.x, t.y, t.z)
    Definitions.transform.scale(1/x,1/y,1/z)
    Definitions.transform.rotate(t.o, t.x, t.y, t.z)
    
    if sensor.type == "EEG":
        Definitions.transform.scale(0.01,0.01,0.01)
    else:
        Definitions.transform.scale(0.03,0.03,0.03)

    Definitions.transform.translate(0.5, 0, 0)
    
    
    """ store transformation in package """
    if sensor.type == "EEG":
        Definitions.packagePreprocess[Graphics.vboCircle] = Definitions.packagePreprocess[Graphics.vboCircle] + [[Definitions.transform.peek(), "Sensor", countID, sensor],]
    elif sensor.type == "Custom":
        Definitions.packagePreprocess[Graphics.vboSphere] = Definitions.packagePreprocess[Graphics.vboSphere] + [[Definitions.transform.peek(), "Sensor", countID, sensor],]
    elif sensor.type == "EMG":
        Definitions.packagePreprocess[Graphics.vboHexagon] = Definitions.packagePreprocess[Graphics.vboHexagon] + [[Definitions.transform.peek(), "Sensor", countID, sensor],]
    else:
        Definitions.packagePreprocess[Graphics.vboPyramide] = Definitions.packagePreprocess[Graphics.vboPyramide] + [[Definitions.transform.peek(), "Sensor", countID, sensor],]
    #Definitions.packageSensors = Definitions.packageSensors + [[Definitions.transform.peek(), sensor],]

    Definitions.transform.pop()
    Definitions.transform.pop()

def drawSensor(style):
    vboId = -1
    for indices in Definitions.packageIndices[2]:
        pack = Definitions.packagePreprocess[indices[0]][indices[1]]
        sensor = pack[Definitions.entity]
        

        """ choose color """
        if style != Graphics.idBuffer:
            color = np.array([sensor.color[0], sensor.color[1], sensor.color[2], 1.], dtype = np.float32)
            if pack[Definitions.packID] == selectedSens:
                pack[Definitions.entity].x += Events.incSens[0]
                pack[Definitions.entity].t += Events.incSens[1]
                pack[Definitions.entity].s += Events.incSens[2]
                if Events.resetSens == True:
                    pack[Definitions.entity].x = 0
                    pack[Definitions.entity].t = 90
                    pack[Definitions.entity].s = 90

                vboDraw = Graphics.vboSurfaces
            elif Cursor.parent == 1 and pack[Definitions.packID] == Cursor.ID:
                vboDraw = Graphics.vboSurfaces
            elif sensor.type == "EEG":
                vboDraw = Graphics.vboSurfaces
            else:
                vboDraw = Graphics.vboEdges
        else:
            vboDraw = Graphics.vboSurfaces
            i = pack[Definitions.packID]/float(countID)
            color = np.array([0, i, 0, 1.], dtype = np.float32)

        #if vboId != indices[0]:
        """ choose vbo """
        vboId = indices[0]
                    
        """ bind surfaces vbo """
        Graphics.indexPositions[vboId][vboDraw].bind()
        Graphics.vertexPositions[vboId].bind()
        glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, None)

            
        
        
        """ send color to shader """
        glUniform4fv(Shaders.setColor_loc, 1, color)

        """ load matrix in shader """
        glUniformMatrix4fv(Shaders.transform_loc, 1, GL_FALSE, pack[Definitions.packTransform])

        """ draw vbo """
        glDrawElements(Graphics.styleIndex[vboId][vboDraw], Graphics.nbIndex[vboId][vboDraw], GL_UNSIGNED_INT, None)


def drawDashed(style):
    vboId = -1
    for indices in Definitions.packageIndices[3]:
        pack = Definitions.packagePreprocess[indices[0]][indices[1]]
        
        if vboId != indices[0]:
            """ choose vbo """
            vboId = indices[0]
                    
            """ bind surfaces vbo """
            if style != Graphics.idBuffer:
                Graphics.indexPositions[vboId][Graphics.vboEdges].bind()
            else:
                Graphics.indexPositions[vboId][Graphics.vboSurfaces].bind()
            Graphics.vertexPositions[vboId].bind()
            glVertexAttribPointer(0, 3, GL_FLOAT, False, 0, None)
            
        """ choose color """
        sensor = pack[Definitions.entity]
        if style != Graphics.idBuffer:
            if Cursor.parent == 1 and pack[Definitions.packID] == Cursor.ID:
                color = np.array([0.,0.,1.,0.3], dtype = np.float32)
            else:
                color = np.array([sensor.color[0], sensor.color[1], sensor.color[2], 1.], dtype = np.float32)
        else:
            i = pack[Definitions.packID]/float(countID)
            color = np.array([0, i, 0, 1.], dtype = np.float32)
            
        """ send color to shader """
        glUniform4fv(Shaders.setColor_loc, 1, color)

        """ load matrix in shader """
        glUniformMatrix4fv(Shaders.transform_loc, 1, GL_FALSE, pack[Definitions.packTransform])
        
        """ draw vbo """
        if style != Graphics.idBuffer:
            glDrawElements(Graphics.styleIndex[vboId][Graphics.vboEdges], Graphics.nbIndex[vboId][Graphics.vboEdges], GL_UNSIGNED_INT, None)
        else:
            glDrawElements(Graphics.styleIndex[vboId][Graphics.vboSurfaces], Graphics.nbIndex[vboId][Graphics.vboSurfaces], GL_UNSIGNED_INT, None)