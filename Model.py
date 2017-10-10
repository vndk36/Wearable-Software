import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *
import OpenGL.GL.shaders

from OpenGL.arrays import vbo
from OpenGL.raw.GL.ARB.vertex_array_object import glGenVertexArrays, \
                                                  glBindVertexArray
from ctypes import *
import numpy as np

import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)

import math
import time
import random
import enum

import Cursor
import Definitions
import Events
import Graphics
import Sensors
import Shaders
import State
import StickMan


part = -1 # global helps through recursivity
""" recursive function that draws body and sensors """
def stick(entity = StickMan.characteristics(), offset = (0,0,0), rotation = (0,0,0,0)):
    global part
    global selectedPart
    if part + 1 >= len(entity.parts):
        return

    part += 1
    current_part = part

    """ Check if part is selected """
    partIsSelected = False
    for selectedPart in StickMan.selectedParts:
        if selectedPart == entity.parts[current_part][StickMan.Data_id]:
            partIsSelected = True
            break


    """ default orientation of part """
    l = Definitions.vector4D.Eul2Quat(Definitions.vector4D((0, entity.parts[current_part][StickMan.Data_angleRepos][0], entity.parts[current_part][StickMan.Data_angleRepos][1], entity.parts[current_part][StickMan.Data_angleRepos][2])))

    """ current rotation of part """
    m = Definitions.vector4D((entity.parts[current_part][StickMan.Data_angle]))
    
    """ resulting orientation of part """
    q = m

    """ new rotation to implement """
    n = Definitions.vector4D.Eul2Quat(Definitions.vector4D((0, 0, 0, 0)))
    if partIsSelected == True:
        """ the rotation command """
        n = Definitions.vector4D.Eul2Quat(Definitions.vector4D((0, Events.pivot[0], Events.pivot[1], Events.pivot[2])))

        """ resulting orientation of part ... """
        q = Definitions.vector4D.QuatProd(m,n)

        """ ... with saturations """
        q = Definitions.vector4D.QuatSat(q, (entity.parts[current_part][StickMan.Data_saturation]))

        """ store resulting orientation """
        entity.parts[current_part][StickMan.Data_angle] = [q.o,q.x,q.y,q.z]
    

    """ Transformations """
    glPushMatrix()
    Definitions.transform.push()
    """ offset to apply """
    glTranslatef(offset[0] + entity.size*entity.parts[current_part][StickMan.Data_offset][0], offset[1] + entity.size*entity.parts[current_part][StickMan.Data_offset][1], offset[2] + entity.size*entity.parts[current_part][StickMan.Data_offset][2])
    Definitions.transform.translate(offset[0] + entity.size*entity.parts[current_part][StickMan.Data_offset][0], offset[1] + entity.size*entity.parts[current_part][StickMan.Data_offset][1], offset[2] + entity.size*entity.parts[current_part][StickMan.Data_offset][2])
    """ total rotation to apply """
    p = Definitions.vector4D.Quat2Vec(Definitions.vector4D.QuatProd(l,q))
    if math.sqrt(p.x*p.x + p.y*p.y + p.z*p.z) >= 0.0001:
        glRotatef(p.o, p.x, p.y, p.z)
        Definitions.transform.rotate(p.o, p.x, p.y, p.z)
        
        
    """ preprocess part """
    x = entity.size*entity.parts[current_part][StickMan.Data_dimensions][0]
    y = entity.size*entity.parts[current_part][StickMan.Data_dimensions][1]
    z = entity.size*entity.parts[current_part][StickMan.Data_dimensions][2]
    dx = 0.5*entity.size*entity.parts[current_part][StickMan.Data_dimensions][0]
    dy = 0
    dz = 0
    StickMan.preprocessPart(x,y,z,dx,dy,dz,partIsSelected, entity.parts[current_part][StickMan.Data_id])

    """ preprocess sensors """
    for sensor in Sensors.virtuSens:
        if sensor.attach == entity.parts[current_part][StickMan.Data_id]:
            sensor.h = 0.707*max(entity.size*entity.parts[current_part][StickMan.Data_dimensions][1],entity.size*entity.parts[current_part][StickMan.Data_dimensions][2])
            """ store transformation in package """
            Definitions.packageSensors = Definitions.packageSensors + [[Definitions.transform.peek(), sensor],]


    """ recursive call for all parts attached to the current one """
    while part + 1 < len(entity.parts) and entity.parts[part+1][StickMan.Data_layer] > entity.parts[current_part][StickMan.Data_layer]:
        stick(entity, (x, 0, 0), (0,0,0,0))

    glPopMatrix()
    Definitions.transform.pop()



def main():
    global part
    
    """ Create list of models """
    State.createList()

    """ Create Entities """
    StickMan.virtuMan = StickMan.characteristics(1.7, (0,0,0), StickMan.parts)
    State.load(StickMan.virtuMan)
    Sensors.virtuSens = [Sensors.sensors("Forearm_r", (0,0), (1,1,0)), Sensors.sensors("Forearm_l", (0.1,90), (0,1,0)), Sensors.sensors("Head", (0.1,45)), Sensors.sensors("Forearm_l", (0.2,240)), Sensors.sensors("Upp_leg_r", (0.1,240)), Sensors.sensors("Head", (0.2,300), (0,0,1)), Sensors.sensors("Head", (0.15,160), (1,0,0.5)), Sensors.sensors("Head", (0.15,200), (1,0,0.5))]

    """ Create a window """
    pygame.init()
    screen = pygame.display.set_mode(Events.display, pygame.DOUBLEBUF|pygame.OPENGL|pygame.OPENGLBLIT|RESIZABLE|NOFRAME)
    
    """ texture """
    # create texture
    plane_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, plane_texture)
    # texture wrapping parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    # texture filtering parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, Events.display[0], Events.display[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
    glBindTexture(GL_TEXTURE_2D, 0)

    """ render buffer for depth """
    # create render buffer
    rbo = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, Events.display[0], Events.display[1])
    glBindRenderbuffer(GL_RENDERBUFFER, 0)
    
    """ frame buffer object """
    # create frame buffer
    FBO = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, FBO)
    # attach texture to frame buffer
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, plane_texture, 0)
    # attach render buffer to frame buffer
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

    
    """ Generate the VBOs """
    Graphics.VBO_init()
    #       positions           colors          texture?
    cube = [-0.5, -0.5, -0.5,   1., 0., 0.,
             0.5, -0.5, -0.5,   0., 1., 0.,
             0.5,  0.5, -0.5,   0., 0., 1.,
            -0.5,  0.5, -0.5,   1., 1., 1.,
            -0.5, -0.5,  0.5,   1., 0., 0.,
             0.5, -0.5,  0.5,   0., 1., 0.,
             0.5,  0.5,  0.5,   0., 0., 1.,
            -0.5,  0.5,  0.5,   1., 1., 1.]
    cube = np.array(cube, dtype = np.float32)
    indices = [0, 1, 2, 2, 3, 0,
               4, 5, 6, 6, 7, 4,
               4, 5, 1, 1, 0, 4,
               6, 7, 3, 3, 2, 6,
               5, 6, 2, 2, 1, 5,
               7, 4, 0, 0, 3, 7]
    indices = np.array(indices, dtype = np.uint32)

    VBO_test = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, VBO_test)
    glBufferData(GL_ARRAY_BUFFER, len(cube)*4, cube, GL_STATIC_DRAW)

    EBO_test = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_test)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices)*4, indices, GL_STATIC_DRAW)

    
    """ Create the shaders """
    Shaders.shader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(Shaders.vertex_shader,GL_VERTEX_SHADER),
                                                      OpenGL.GL.shaders.compileShader(Shaders.fragment_shader,GL_FRAGMENT_SHADER))
    glUseProgram(Shaders.shader)


    position = glGetAttribLocation(Shaders.shader, "position")
    glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0*4))
    glEnableVertexAttribArray(position)

    color = glGetAttribLocation(Shaders.shader, "color")
    glVertexAttribPointer(color, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(3*4))
    glEnableVertexAttribArray(color)


    """ Initialize some more stuff"""
    
    glEnable(GL_TEXTURE_2D)
    glDepthFunc(GL_LEQUAL)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_DEPTH_TEST)
    
    

    """ Shader var. locations """
    Shaders.proj_loc = glGetUniformLocation(Shaders.shader, "projection")
    Shaders.view_loc = glGetUniformLocation(Shaders.shader, "view")
    Shaders.model_loc = glGetUniformLocation(Shaders.shader, "model")
    Shaders.transform_loc = glGetUniformLocation(Shaders.shader, "transform")
    Shaders.setColor_loc = glGetUniformLocation(Shaders.shader, "setColor")
    
    Definitions.projectionMatrix.perspectiveProjection(90, Events.display[0]/Events.display[1], 0.1, 100.0)
    glUniformMatrix4fv(Shaders.proj_loc, 1, GL_FALSE, Definitions.projectionMatrix.peek())
    glUniformMatrix4fv(Shaders.model_loc, 1, GL_FALSE, Definitions.modelMatrix.peek())

    """ main loop """
    while True:
        
        flagStart = time.clock()
        

        """
            Events management.
            Every interaction between the user and the software is aknowledged here.
        """
        Events.manage()



        """
            Preprocess entities.
            Store all needed transformations to significantly lower calculation cost when rendering (redundancy otherwise between display buffer, ID buffer and bindings)
        """
        part = -1 # initialize the recursivity here
        stick(StickMan.virtuMan, (StickMan.virtuMan.x, StickMan.virtuMan.y, StickMan.virtuMan.z))



        """ 
            Draw on the ID buffer.
            The ID BUFFER is used for the mouse implementation, to know which part is targeted with the cursor.
        """
        # bind the ID buffer
        glBindFramebuffer(GL_FRAMEBUFFER, FBO)
        
        # clear the ID buffer
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        # fill ID buffer
        Graphics.modelView(Graphics.opaque)
        StickMan.drawStickMan(Graphics.idBuffer)
        Sensors.displaySensor(Graphics.idBuffer)

        


        """
            cursor feedback.
            Read the value of the ID buffer at mouse position.
        """
        color = glReadPixels( Cursor.mouse[0] , Events.display[1] - Cursor.mouse[1] - 1 , 1 , 1 , GL_RGB , GL_FLOAT )
        ID = 0
        if color[0][0][0] != 0: # RED channel for parts ID
            ID = color[0][0][0]*len(Definitions.packageStickMan)
        elif color[0][0][1] != 0: # GREEN channel for sensors ID
            ID = color[0][0][1]*len(Definitions.packageSensors) + 1
        
        #convert float to int with errors management
        if ID < 0.5:
            ID = 0
        elif ID - int(ID) >= 0.5:
            ID = int(ID + 0.5)-1
        else:
            ID = int(ID)-1

        # select part
        if color[0][0][0] != 0:
            Definitions.packageStickMan[ID][1] = True
        


        """
            Draw on the display buffer.
            The display buffer is what the user will see on his screen.
        """
        # bind the display buffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        # clear the display buffer
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        # draw scene
        Graphics.modelView(Graphics.blending)
        Graphics.displayGround(math.fabs(Events.rMax))

        # draw body
        Graphics.modelView(Events.style)
        StickMan.drawStickMan(Events.style)

        # draw sensors
        Graphics.modelView(Graphics.opaque)
        Sensors.displaySensor(Events.style)
        
        # draw text
        Graphics.textTexture(str(ID))
        

        # update display buffer
        pygame.display.flip()

        """
            empty preprocess packages
        """
        while len(Definitions.packageStickMan) > 0:
            Definitions.packageStickMan = Definitions.packageStickMan[:-1]
        while len(Definitions.packageSensors) > 0:
            Definitions.packageSensors = Definitions.packageSensors[:-1]



        pygame.time.wait(10)

        #print(1./(time.clock()-flagStart))

        


main()