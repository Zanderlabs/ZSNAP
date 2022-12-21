# -*- coding: utf-8 -*-
from framework import LatentModule
from panda3d.core import TextProperties, TextPropertiesManager

"""
@authors    TSE, AGC
@org        ZLS
@date       2022-12-21
"""

"""
Fixation cross for resting state conditions.

"""

"""
Changelog
2022-08-25 first version 
"""

global base


class Main(LatentModule):
    def __init__(self):
        LatentModule.__init__(self)

        self.moduleName = "Rest"

        self.trials = 1  # number of trials in total
        self.trialLength = 1  # length of one trial in seconds (needs to be at least one)
        self.blockLength = 1  # number of trial before pause

        self.taskScale = .1  # text scale of presented task

        self.textPressSpace = "Press space to continue"  # text to display before each block
        self.textExperimentEnd = "End of this part"  # text to display at the end of the experiment
        self.fontFace = "arial.ttf"  # text font
        self.textColour = (0.5, 0.5, 0.5, 1)  # text colour (r, g, b, a)
        self.textBgColour = (0, 0, 0, .75)  # text background colour
        self.textScale = .1  # text scale

        self.crossTime = 125  # length in seconds that the crosshair is visible before each block
        self.crossScale = 0.15  # size of the crosshair
        self.crossColour = (.5, .5, .5, 1)  # colour of the crosshair

        self.framerate = 60  # in Hz
        self.fadeTime = 1  # time that sparkles/tasks take to fade in/out, in seconds

    def waitForUser(self):
        # waiting for user to be ready
        self.write(
            text="\1text\1" + self.textPressSpace,
            font=self.fontFace,
            scale=self.textScale,
            fg=self.textColour,
            bg=self.textBgColour,
            duration='space')

    def crossOn(self):
        # fading cross in
        self.crossGraphics = self._engine.direct.gui.OnscreenImage.OnscreenImage(
            image='cross.png',
            scale=self.crossScale,
            color=(self.crossColour[0], self.crossColour[1], self.crossColour[2], 0))
        self.crossGraphics.setTransparency(1)

        for i in range(self.fadeFrames):
            self.crossGraphics.setColor((self.crossColour[0], self.crossColour[1], self.crossColour[2],
                                         self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)

    def crossOff(self):
        # fading cross out
        for i in range(self.fadeFrames):
            self.crossGraphics.setColor((self.crossColour[0], self.crossColour[1], self.crossColour[2],
                                         self.crossColour[3] - self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)

        self.crossGraphics.destroy()

    def run(self):
        self.accept("escape", self.exit)

        # setting black background color
        base.win.setClearColor((0, 0, 0, 1))

        # setting text color
        tp = TextProperties()
        tp.setTextColor(self.textColour)
        tpMgr = TextPropertiesManager.getGlobalPtr()
        tpMgr.setProperties("text", tp)

        # setting fade length in frames
        self.fadeFrames = int(self.framerate * self.fadeTime)

        """ MAIN LOOP """
        for trial in range(self.trials):
            # implementing pause between blocks
            if trial % self.blockLength == 0:
                self.waitForUser()

                # showing crosshair
                self.crossOn()
                # wait with cross on
                self.sleep(self.crossTime)
                # removing crosshair
                self.crossOff()

        # end of experiment
        self.write(
            text="\1text\1" + self.textExperimentEnd,
            duration='space')

    def exit(self):
        print("Exiting...")
        exit()
