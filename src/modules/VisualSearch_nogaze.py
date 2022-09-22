#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author     TSE
@org        ZLS
@date       2022-08-25
"""

"""
Visual search paradigm with Where is Waldo/Wally images.

"""

"""
Changelog
2022-08-25 first version  - edited from VisIntOdd by lrk
"""

from direct.gui.DirectGui import DirectEntry
from framework.latentmodule import LatentModule
from panda3d.core import TextProperties, TextPropertiesManager
from random import choice, random, sample, shuffle, uniform
from time import time
from os import listdir
from math import floor, isnan


class Main(LatentModule):
    def __init__(self):
        LatentModule.__init__(self)

        # read images for stimuli
        self.waldoimagepath = "./media/waldo/images/"   # image path
        self.waldomaskpath  = "./media/waldo/masks/"     # mask path
        self.waldocharpath  = "./media/waldo/ch/"        # character path
        self.waldoimages = listdir(self.waldoimagepath) # read available images 
        shuffle(self.waldoimages)                       # shuffle images in order
        #self.waldoimages =  ["book1-part1_ch1_blank.png"]
        
        self.alltrials = len(self.waldoimages)                  # all trials
        self.blocks = 12                                         # number of blocks
        self.ntrialperblock = floor(self.alltrials/self.blocks) # max integer number of images per block
        self.trials = int(self.ntrialperblock*self.blocks)      # integer number of trials
        
        # Waldo/Wally # Wenda # White beard # Odlaw
        self.waldotarget =  ["./media/waldo/ch/ch1_b.png", "./media/waldo/ch/ch2_b.png" , "./media/waldo/ch/ch3_b.png", "./media/waldo/ch/ch4_b.png" ] 
        self.targetduration = 1   # duration on screen 
        
        self.moduleName = "VisualSearch"

        self.backgroundColour = (0, 0, 0, 1)        # background colour

        self.logging = True                         # whether or not to write log files

        self.instruction = False                    # whether or not to provide instructions and a training phase
        self.language = 0                           # 0 = english
        self.instructionText = [[
                "English instructions here."
                ], [
                "Deutsche Instruktionen hier."
                ]]

        self.pauseafterblocks = 1                   # self-paced break after this number of blocks (1 = each)

        self.maxtime = 6                           # maximum trial duration (to skip a trial)

        self.fontFace = "arial.ttf"                     # text font
        self.textScale = .1                             # text scale
        self.textColour = (.5, .5, .5, 1)               # text colour
        self.textBgColour = (0, 0, 0, .75)              # text background colour
        self.textPressSpace = "Press space to continue" # text to display at user prompts
        self.textExperimentEnd = "End of this part"     # text to display at the end of the experiment

        self.photomarkerColour = (1, 1, 1, 1)           # photomarker colour
        self.photomarkerScale = .1                      # photomarker scale
        self.photomarkerDuration = .15                  # photomarker duration in seconds
        self.photomarkerPosition = "lr"                 # default photomarker position:
                                                        # tl = top left
                                                        # ll = lower left
                                                        # tr = top right
                                                        # lr = lower right
                                                        
        self.crossTime = [0.5, 0.9]             # duration range in seconds that the crosshair is visible before each block
        self.crossScale = 0.15                   # size of the crosshair
        self.crossColour = (.5, .5, .5, 1)      # colour of the crosshair
        
        self.blanktime = [1, 1.5]
        
        self.framerate = 60                 # in Hz
        self.fadeTime  = 0.1                # time that sparkles/tasks take to fade in/out, in seconds
        
        self.currenttrial = 0     # main index for trials
        
        self.cursorAlpha = 0.4
        self.cursorScale = 0.05
        self.cursorPos = (0,0,0)
        self.cursorColor = (0.92, 0.04, 0.56)
        
        
        # image scale
        #pixelsX = GetSystemMetrics(0)
        #pixelsY = GetSystemMetrics(1)

    def waitForUser(self):
        # waiting for user to be ready
        self.write(
                text = "\1text\1" + self.textPressSpace,
                font = self.fontFace,
                scale = self.textScale,
                fg = self.textColour,
                bg = self.textBgColour,
                duration = 'space')
                
    def crossOn(self):
        # fading cross in
        self.crossGraphics = self._engine.direct.gui.OnscreenImage.OnscreenImage(
                image = 'cross.png',
                scale = self.crossScale,
                color = (self.crossColour[0], self.crossColour[1], self.crossColour[2], 0))
        self.crossGraphics.setTransparency(1)
        
        for i in range(self.fadeFrames):
            self.crossGraphics.setColor((self.crossColour[0], self.crossColour[1], self.crossColour[2], self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)
        
    def crossOff(self):
        # fading cross out
        for i in range(self.fadeFrames):
            self.crossGraphics.setColor((self.crossColour[0], self.crossColour[1], self.crossColour[2], self.crossColour[3] - self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)
            
        self.crossGraphics.destroy()   
        
    def showCursor(self):
        # show cursor on top of the screen
        self.cursor = self._engine.direct.gui.OnscreenImage.OnscreenImage(
                image = 'circle.png',
                scale = self.cursorScale,
                pos = self.cursorPos)
        self.cursor.setTransparency(1)
       
        for i in range(self.fadeFrames):
            self.cursor.setColor((self.cursorColor[0],self.cursorColor[1],self.cursorColor[2], self.cursorAlpha * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)
            
    def updateCursor(self):
        self.cursor.destroy()
        self.cursor = self._engine.direct.gui.OnscreenImage.OnscreenImage(
                image = 'circle.png',
                scale = self.cursorScale,
                pos = self.cursorPos)
        self.cursor.setTransparency(1)
        self.cursor.setColor((self.cursorColor[0],self.cursorColor[1],self.cursorColor[2], self.cursorAlpha))
        
    def removeCursor(self):
        # remove cursor 
        self.cursor.destroy() 
        
        
    def run(self):
        
        # accepting keyboard input
        self.accept("escape", self.exit)

        # setting background colour
        base.win.setClearColor(self.backgroundColour)        
        
        # setting fade length in frames
        self.fadeFrames = int(self.framerate * self.fadeTime)

        # configuring smaller text for instructions
        tp = TextProperties()
        tp.setTextScale(.5)
        tpMgr = TextPropertiesManager.getGlobalPtr()
        tpMgr.setProperties("small", tp)

        if self.logging:
            # subject entry elements
            self.text = self._engine.direct.gui.OnscreenText.OnscreenText(
                    text = " Participant #   ",
                    scale = self.textScale,
                    fg = self.textColour,
                    bg = self.textBgColour,
                    pos = (0, 0))
            self.entry = DirectEntry(
                    focus = 1,
                    width = 3,
                    scale = self.textScale,
                    pos = (0, 0, -self.textScale * 1.5),
                    text_fg = self.textColour,
                    frameColor = self.textBgColour,
                    command = self.setSubject)
            self.write(
                    text = "",
                    duration = "enter")

            # creating main log file, writing variable names
            openTime = str(long(time() * 1000))
            self.logFile = "./logs/" + self.moduleName + "-" + openTime + "-" + self.subject + ".csv"
            logfile = open(self.logFile, "w")
            logfile.write('"subject";"timestamp";"block";"trial";"stimulusfile"')
            logfile.close()
        
        """ training """

        if self.instruction:
            pass
        
        # setting visual search steps 
        self.visualsearchframes = int(self.framerate * self.maxtime)
        
        
        """ main loop """
        for block in range(self.blocks):
            for trial in range(self.trials):
            
                if trial % self.ntrialperblock == 0:  # number of trials divided by trials per block (zero every block)
                    # self-paced break
                    self.waitForUser()
                    self.sleep(1)

                showthisimage = self.waldoimages[trial] # indicate which image to show
                usethismask  = showthisimage[0:len(showthisimage)-4] + '_mask.png' # corresponding mask
            
                print showthisimage
                print usethismask
            
                # log image
                self.log(block+1,trial+1, showthisimage)
            
                # which target?
                if 'ch1' in showthisimage:
                    thistarget = self.waldotarget[0]
                if 'ch2' in showthisimage:
                    thistarget = self.waldotarget[1]
                if 'ch3' in showthisimage:
                    thistarget = self.waldotarget[2]
                if 'ch4' in showthisimage:
                    thistarget = self.waldotarget[3]
                
                print thistarget
            
                # run trial
            
                self.crossOn()
                self.sleep(uniform(self.crossTime[0], self.crossTime[1]))
                self.crossOff()
            
                self.photomarker("target")
                self.picture(thistarget, duration=self.targetduration, pos = [0,0,0], scale=[0.126,1,0.2], color=self.photomarkerColour)
            
                self.crossOn()
                self.sleep(uniform(self.crossTime[0], self.crossTime[1]))
                self.crossOff()
            
                # show location during debug 
                # self.picture(self.waldomaskpath + usethismask, duration=0.3, pos = [0,0,0], scale=[1.5,1,0.95], color=self.photomarkerColour)
                self.photomarker("image")
                self.picture(self.waldoimagepath + showthisimage, duration=self.maxtime, pos = [0,0,0], scale=[1.5,1,0.95], color=self.photomarkerColour, block = False) 
            
                onTargetCount = 0
            
                # show cursor
                for f in range(self.visualsearchframes):
            
                 
                    if f == 0:
                        self.showCursor()
                    else:
                        self.updateCursor()
                    
                    # check if gaze is on target
                    #if onTargetCount == 200:
                    #    print "should stop"
                    #    self.removeCursor()
                    #    break
                    #    
                    #onTargetCount = onTargetCount + 1    
                    #print onTargetCount   
                    self.sleep(1.0 / self.framerate)
                
                self.removeCursor()
                self.sleep(uniform(self.blanktime[0], self.blanktime[1]))
                self.cursorPos = (0,0,0)
                
        """ end main loop """
        
        # end of experiment
        self.write(
                text = "\1text\1" + self.textExperimentEnd,
                duration = 'space')


    def show_feedback(self, posneg):
        # presenting positive/negative feedback
        if posneg:
            file = self.feedbackposfile
        else:
            file = self.feedbacknegfile

        self.sleep(self.beforefeedbacktime + (random() * 2 - 1) * self.beforefeedbacktimedev)
        self.photomarker("feedback" + str(posneg))
        self.picture(file, duration=self.feedbacktime, scale=self.feedbacksize, color=self.feedbackcolor)


    def waitForUser(self):
        # waiting for user to be ready
        self.write(
                text = self.textPressSpace,
                font = self.fontFace,
                scale = self.textScale,
                fg = self.textColour,
                bg = self.textBgColour,
                duration = "space")


    def setSubject(self, subject):
        # removing subject entry elements, setting subject variable
        self.text.destroy()
        self.entry.destroy()
        self.subject = subject


    def instruct(self, text, time=0):
        # writing instructions on the screen, either for given number of
        # seconds, or until the user presses space
        if time == 0:
            text = text + "\n\n\1small\1" + self.textPressSpace

        # writing instructions on the screen
        text = self.write(
                text = text,
                font = self.fontFace,
                scale = self.textScale,
                fg = self.textColour,
                bg = self.textBgColour,
                wordwrap = 25,
                duration = 0,
                block = False)
        self.alignVertical(text, 1)

        if time == 0: self.waitfor("space")
        else:         self.sleep(time)

        text.destroy()


    def alignVertical(self, object, align = 1):
        # helper function for vertical alignment of text
        # 0 = top, 1 = center, 2 = bottom
        b = object.getTightBounds()
        z = [1-b[1][2], -(b[1]+b[0])[2]*.5, -b[0][2]-1]
        object.setZ(z[align])


    def photomarker(self, marker, position = None):
        # sending generic LSL marker
        self.marker(marker)

        # flashing coloured square to be picked up by photo sensor
        if position is None: position = self.photomarkerPosition

        ar = base.getAspectRatio()
        sc = self.photomarkerScale

        if position == "tl":
            rect = [-ar, sc-ar, 1, 1-sc]
        elif position == "ll":
            rect = [-ar, sc-ar, sc-1, -1]
        elif position == "tr":
            rect = [ar-sc, ar, 1, 1-sc]
        elif position == "lr":
            rect = [ar-sc, ar, sc-1, -1]

        self.rectangle(
                rect = rect,
                duration = self.photomarkerDuration,
                color = self.photomarkerColour,
                block = False)


    def log(self, *args):
        if self.logging:
            logfile = open(self.logFile, "a")
            logfile.write("\n" + self.subject + ";" + str(time()) + ";" + ";".join(map(str, args)))
            logfile.close()


    def exit(self):
        print "Exiting..."
        exit()