#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author:         Laurens R. Krol
Organisation:   Team PhyPA, Technische Universitaet Berlin
Version:        1.1.2
Date:           2020-01-28
"""

"""
This is a base template for SNAP modules containing some general functionality:
- Logging function self.log() generates a logfile based on given subject ID, and 
  saves any given variables as semicolon-separated values in that .csv file.
- Self-paced or timed instruction delivery self.instruct() puts vertically-aligned and
  word-wrapped text on the screen.
- A general self-paced break self.waitForUser() halts execution until the user 
  presses the space bar.
- Visual markers self.photomarker(), in addition to calling the regular self.marker,
  generate visual flashes in one of the screen's corners such that these markers can
  be picked up using photo sensors. With the data from these photosensors, the timing
  of the regular markers can be corrected. This is necessary for latency-critical
  experiments, since SNAP/Panda3D has significant lag and jitter.

SNAP is an experiment scripting environment written by Christian Kothe,
based on the Panda3D engine.
SNAP: https://github.com/sccn/SNAP
Panda3D: https://www.panda3d.org
"""

"""
Changelog
2020-01-28 lrk
  - Updated instruct() method
"""

"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


from direct.gui.DirectGui import DirectEntry
from framework.latentmodule import LatentModule
from panda3d.core import TextProperties, TextPropertiesManager
from time import time
import os
import sys

class Main(LatentModule):
    def __init__(self):
        LatentModule.__init__(self)

        self.moduleName = "BaseModule"
        
        self.backgroundColour = (0, 0, 0, 1)    # background colour
        
        self.logging = True                    # whether or not to write log files
        self.logHeaders = '"subject";"time";"..."' 
                                                # the log file's header line, listing
                                                # all variables as "var1";"var2"; ...
                                                # starting with subject ID and log time
        
        self.fontFace = "arial.ttf"                     # text font
        self.textScale = .1                             # text scale
        self.textColour = (.5, .5, .5, 1)               # text colour
        self.textBgColour = (0, 0, 0, .75)              # text background colour
        self.textPressSpace = "Press space to continue" # text to display at user prompts
        
        self.photomarkerColour = (1, 1, 1, 1)           # photomarker colour
        self.photomarkerScale = .1                      # photomarker scale
        self.photomarkerDuration = .5                   # photomarker duration in seconds
        self.photomarkerPosition = "lr"                 # default photomarker position:
                                                        # tl = top left
                                                        # ll = lower left
                                                        # tr = top right
                                                        # lr = lower right


    def run(self):
        # accepting keyboard input
        self.accept("escape", self.exit)

        # setting background colour
        base.win.setClearColor(self.backgroundColour)
        
        # configuring smaller text for instructions
        tp = TextProperties()
        tp.setTextScale(.5)
        tpMgr = TextPropertiesManager.getGlobalPtr()
        tpMgr.setProperties("small", tp)

        if self.logging:
            # displaying subject entry elements
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
            self.waitfor("enter")
                    
            # creating main log file
            openTime = str(long(time() * 1000))
            self.logFile = os.path.join("logs", self.moduleName + "-" + openTime + "-" + self.subject + ".csv")
            logfile = open(self.logFile, "w")
            logfile.write(self.logHeaders)
            logfile.close()
            
        """ start main loop """
        
        self.instruct("Your experiment here", 1)
        self.instruct("Your experiment here")
        
        """ end main loop """


    def waitForUser(self):
        # waiting for user to be ready and press space
        self.write(
                text = self.textPressSpace,
                font = self.fontFace,
                scale = self.textScale,
                fg = self.textColour,
                bg = self.textBgColour,
                duration = "space")


    def setSubject(self, subject):
        # helper function to set subject ID and remove the input elements
        self.text.destroy()
        self.entry.destroy()
        self.subject = subject

    
    def instruct(self, text, time=0):
        # writing instructions on the screen, either for given number of
        # seconds, or until the user presses space
        if time == 0:
            text = text + "\n\n\1small\1" + self.textPressSpace
        
        text = self.write(
                text = text,
                font = self.fontFace,
                scale = self.textScale,
                fg = self.textColour,
                bg = self.textBgColour,
                wordwrap = 25,
                duration = 0,
                block = False)
        self.alignVertical(text)
        
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
        # logging data to log file along with subject ID and current timestamp
        # e.g. self.log(var1, var2) writes subjectID;timestamp;var1;var2 to the log file.
        # make sure to always log the same variables, and to update self.logHeaders accordingly.
        if self.logging:
            logfile = open(self.logFile, "a")
            logfile.write(self.subject + ";" + str(time()) + ";" + ";".join(map(str, args)) + "\n")
            logfile.close()


    def exit(self):
        print "Exiting..."
        sys.exit()