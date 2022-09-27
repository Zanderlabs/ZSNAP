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
from pylslx import StreamInlet, resolve_stream
from collections import deque
from PIL import Image
import numpy as np


# from pylsl import StreamInfo, StreamOutlet,


def simple_almost_equal(a, b, dec=3):
    return (a == b or
            int(floor(a * 10 ** dec)) == int(floor(b * 10 ** dec)))


class Main(LatentModule):
    def __init__(self):
        LatentModule.__init__(self)

        self.show_cursor = True
        self.show_mask = True

        # read images for stimuli
        self.waldoimagepath = "./media/waldo/images/"  # image path
        self.waldomaskpath = "./media/waldo/masks/"  # mask path
        self.waldocharpath = "./media/waldo/ch/"  # character path
        self.waldoimages = listdir(self.waldoimagepath)  # read available images
        shuffle(self.waldoimages)  # shuffle images inplace

        self.alltrials = len(self.waldoimages)  # all trials
        self.blocks = 12  # number of blocks
        self.ntrialperblock = floor(self.alltrials / self.blocks)  # max integer number of images per block
        self.trials = int(self.ntrialperblock * self.blocks)  # integer number of trials

        # Waldo/Wally # Wenda # White beard # Odlaw
        self.waldotarget = ["./media/waldo/ch/ch1_b.png",
                            "./media/waldo/ch/ch2_b.png",
                            "./media/waldo/ch/ch3_b.png",
                            "./media/waldo/ch/ch4_b.png"]

        self.moduleName = "VisualSearch"

        self.backgroundColour = (0, 0, 0, 1)  # background colour

        self.logging = True  # whether to write log files

        self.instruction = False  # whether to provide instructions and a training phase
        self.language = 0  # 0 = english
        self.instructionText = [[
            "English instructions here."
        ], [
            "Deutsche Instruktionen hier."
        ]]

        self.pauseafterblocks = 1  # self-paced break after this number of blocks (1 = each)

        self.target_time = 1  # duration on screen
        self.image_time = 20  # maximum trial duration in seconds (to skip a trial)
        self.blank_time = [3, 3.5]  # the blank time
        self.fixation_time = 1  # time in seconds for a fixation to be concluded

        self.fontFace = "arial.ttf"  # text font
        self.textScale = .1  # text scale
        self.textColour = (.5, .5, .5, 1)  # text colour
        self.textBgColour = (0, 0, 0, .75)  # text background colour
        self.textPressSpace = "Press space to continue"  # text to display at user prompts
        self.textExperimentEnd = "End of this part"  # text to display at the end of the experiment

        self.photomarkerColour = (1, 1, 1, 1)  # photo marker colour = full white
        self.photomarkerScale = .1  # photo marker scale = 10%
        self.photomarker_time = .15  # photo marker duration in seconds
        self.photomarkerPosition = "lr"  # default photo marker position, where to show it
        # tl = top left # ll = lower left # tr = top right # lr = lower right

        self.crossTime = [0.5, 0.9]  # duration range in seconds that the crosshair is visible before each block
        self.crossScale = 0.15  # size of the crosshair
        self.crossColour = (.5, .5, .5, 1)  # colour of the crosshair

        self.margin = 0.8
        self.circleTime = [0.5, 0.9]  # duration range in seconds that the crosshair is visible before each block
        self.circleScale = 0.1  # size of the circle
        self.circleColour = (.5, .5, .5, 1)  # colour of the crosshair

        self.framerate = 600  # in Hz
        self.fadeTime = 0.1  # time that sparkles/tasks take to fade in/out, in seconds

        self.currenttrial = 0  # main index for trials

        self.cursor = None
        self.cursorAlpha = 0.4
        self.cursorScale = 0.05
        self.cursorPos = (0, 0, 0)
        self.cursorColor = (0.92, 0.04, 0.56)

        # Scene size
        self.scene_sx = float(base.win.getXSize())
        self.scene_sy = float(base.win.getYSize())
        self.scene_ar = float(self.scene_sx / self.scene_sy)

    def screen2scene(self, x, y):
        return (2 * x / self.scene_sx - 1) * self.scene_ar, -2 * y / self.scene_sy + 1

    def screen2image(self, x, y, im_width, im_height):
        return int(float(x) / self.scene_sx * im_width), int(float(y) / self.scene_sy * im_height)

    def waitForUser(self):
        # waiting for user to be ready
        self.write(
            text="\1text\1" + self.textPressSpace,
            font=self.fontFace,
            scale=self.textScale,
            fg=self.textColour,
            bg=self.textBgColour,
            duration='space')

    def circleOn(self, pos=(0, 0)):
        # fading cross in
        self.circleGraphics = self._engine.direct.gui.OnscreenImage.OnscreenImage(
            image='circle.png',
            scale=self.circleScale,
            pos=[pos[0], 0, pos[1]],
            color=(self.circleColour[0], self.circleColour[1], self.circleColour[2], 0))
        self.circleGraphics.setTransparency(1)

        for i in range(self.fadeFrames):
            self.circleGraphics.setColor((self.circleColour[0],
                                          self.circleColour[1],
                                          self.circleColour[2],
                                          self.circleColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)

    def circleOff(self):
        # fading circle out
        for i in range(self.fadeFrames):
            self.circleGraphics.setColor((self.circleColour[0],
                                          self.circleColour[1],
                                          self.circleColour[2],
                                          self.circleColour[3] - self.circleColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)

        self.circleGraphics.destroy()

    def crossOn(self, pos=(0, 0)):
        # fading cross in
        self.crossGraphics = self._engine.direct.gui.OnscreenImage.OnscreenImage(
            image='cross.png',
            pos=[pos[0], 0, pos[1]],
            scale=self.crossScale,
            color=(self.crossColour[0], self.crossColour[1], self.crossColour[2], 0))
        self.crossGraphics.setTransparency(1)

        for i in range(self.fadeFrames):
            self.crossGraphics.setColor((self.crossColour[0],
                                         self.crossColour[1],
                                         self.crossColour[2],
                                         self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)

    def crossOff(self):
        # fading cross out
        for i in range(self.fadeFrames):
            self.crossGraphics.setColor((self.crossColour[0], self.crossColour[1], self.crossColour[2],
                                         self.crossColour[3] - self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(1.0 / self.framerate)

        self.crossGraphics.destroy()

    def showCursor(self, pos):
        # Check if this is already an update
        cursor_update = self.cursor is not None

        if cursor_update:
            self.cursor.destroy()

        # show cursor on top of the screen
        self.cursor = self._engine.direct.gui.OnscreenImage.OnscreenImage(
            image='circle.png',
            scale=self.cursorScale,
            pos=pos)
        self.cursor.setTransparency(1)

        # is this is the first time we show the cursor then fade it in
        if not cursor_update:
            for i in range(self.fadeFrames):
                self.cursor.setColor((self.cursorColor[0], self.cursorColor[1], self.cursorColor[2],
                                      self.cursorAlpha * float(i) / self.fadeFrames))
                # sleep to allow the scree to update
                self.sleep(0.8 / self.framerate)
        else:
            self.cursor.setColor((self.cursorColor[0], self.cursorColor[1], self.cursorColor[2], self.cursorAlpha))

    def removeCursor(self):
        # destroy the cursor
        if self.cursor is not None:
            self.cursor.destroy()
            self.cursor = None

    def wait4fixation(self, gaze_inlet, duration, max_duration, limit=0.9,
                      mask_array=None, location=(0, 0), radius=0.05, scene_coord=True):

        max_frames = self.framerate * max_duration
        fix_frames = self.framerate * duration
        deq = deque(maxlen=fix_frames)
        for f in range(max_frames):
            # flush the lsl input stream, not yet sure why
            gaze_inlet.flush()

            # get enough to decide whether fixation took place
            # sample, timestamp = inlet.pull_sample()
            eg_sample, eg_timestamp = gaze_inlet.pull_chunk(max_samples=fix_frames)

            if self.show_cursor:
                # calculate the current gaze location
                if len(eg_sample) > 0:
                    curr_gaze = self.screen2scene((eg_sample[-1][0] + eg_sample[-1][2]) / 2,
                                                  (eg_sample[-1][1] + eg_sample[-1][3]) / 2)
                    # show the current gaze location if required
                    # print ('Position {} \r'.format((curr_gaze[0], 0, curr_gaze[1])))
                    self.showCursor((curr_gaze[0], 0, curr_gaze[1]))
                    # wait for the screen to get updated
                    self.sleep(.8 / self.framerate)

            # check if enough gaze was on target,
            # namely more than 90% of the fixation time was on or around the target (a white mask pixel)
            # skip = int(0.1*fix_frames)
            for i, gs in enumerate(eg_sample):
                deq.append(gs)
                # if skip != 0 and i % skip != 0:
                #     continue
                if len(deq) == fix_frames:
                    if mask_array is not None:
                        im_coord = np.array([self.screen2image((x1 + x2) / 2, (y1 + y2) / 2,
                                                               mask_array.shape[1], mask_array.shape[0])
                                             for (x1, y1, x2, y2) in deq])
                        # print(sum(mask_array[im_coord[:, 1], im_coord[:, 0]]), " / ", limit * fix_frames)
                        if sum(mask_array[im_coord[:, 1], im_coord[:, 0]]) > limit * fix_frames:
                            print("Fixation found, going to the next task")
                            return True
                    elif scene_coord:
                        sce_coord = np.array([self.screen2scene((x1 + x2) / 2, (y1 + y2) / 2)
                                              for (x1, y1, x2, y2) in deq])
                        dists = np.linalg.norm(sce_coord - location, axis=1)
                        # print(np.sum(dists < radius), " / ", limit * fix_frames)
                        if np.sum(dists < radius) > limit * fix_frames:
                            print("Fixation found, going to the next task")
                            return True
                    else:
                        scr_coord = np.array([((x1 + x2) / 2, (y1 + y2) / 2)
                                              for (x1, y1, x2, y2) in deq])
                        dists = np.linalg.norm(scr_coord - location, axis=1)
                        # print(np.sum(dists < radius), " / ", limit * fix_frames)
                        if np.sum(dists < radius) > limit * fix_frames:
                            print("Fixation found, going to the next task")
                            return True

        return False

    def run(self):

        # first resolve GAZE streams on the lab network
        print("looking for a GAZE stream...")
        streams = resolve_stream('type', 'Gaze')

        # create a new inlet to read from the stream
        inlet = StreamInlet(streams[0])

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
                text=" Participant #   ",
                scale=self.textScale,
                fg=self.textColour,
                bg=self.textBgColour,
                pos=(0, 0))
            self.entry = DirectEntry(
                focus=1,
                width=3,
                scale=self.textScale,
                pos=(0, 0, -self.textScale * 1.5),
                text_fg=self.textColour,
                frameColor=self.textBgColour,
                command=self.setSubject)
            self.write(
                text="",
                duration="enter")

            # creating main log file, writing variable names
            openTime = str(long(time() * 1000))
            self.logFile = "./logs/" + self.moduleName + "-" + openTime + "-" + self.subject + ".csv"
            logfile = open(self.logFile, "w")
            logfile.write('"subject";"timestamp";"block";"trial";"stimulusfile"')
            logfile.close()

        """ training """

        if self.instruction:
            pass

        """ main loop """
        for block in range(self.blocks):
            for trial in range(self.trials):

                if trial % self.ntrialperblock == 0:  # number of trials divided by trials per block (zero every block)
                    # self-paced break
                    self.waitForUser()
                    self.sleep(1)

                showthisimage = self.waldoimages[trial]  # indicate which image to show
                usethismask = showthisimage[0:len(showthisimage) - 4] + '_mask.png'  # corresponding mask

                print showthisimage
                print usethismask

                # log image
                self.log(block + 1, trial + 1, showthisimage)

                # which target?
                if 'ch1' in showthisimage:
                    thistarget = self.waldotarget[0]
                if 'ch2' in showthisimage:
                    thistarget = self.waldotarget[1]
                if 'ch3' in showthisimage:
                    thistarget = self.waldotarget[2]
                if 'ch4' in showthisimage:
                    thistarget = self.waldotarget[3]

                print (thistarget)

                # ##########################
                # run next trial
                # ##########################
                # Show the cross in the middle of the screen where the target will show up
                self.crossOn(pos=[0, 0])
                self.sleep(uniform(self.crossTime[0], self.crossTime[1]))
                self.crossOff()

                # show the target character - first show a flashing rectangle and send a marker to LSL
                self.photomarker("target")
                self.picture(thistarget, duration=self.target_time, pos=[0, 0, 0], scale=[0.126, 1, 0.2],
                             color=self.photomarkerColour, block=True)

                # Show a circle in a random position and wait until the user has fixated it
                pos = [uniform(0, self.margin * self.scene_sx), uniform(0, self.margin * self.scene_sy)]
                sce_pos = self.screen2scene(pos[0], pos[1])
                self.circleOn(pos=sce_pos)
                self.wait4fixation(gaze_inlet=inlet, duration=self.fixation_time, max_duration=30,
                                   location=sce_pos, scene_coord=True, radius=.15)
                self.circleOff()

                # show the book image to search for the character
                # Load the mask image
                maskfile = Image.open(self.waldomaskpath + usethismask)
                maskfile.load()
                mask_image_array = np.asarray(maskfile, dtype=int)
                image_width, im_height = Image.open(self.waldoimagepath + showthisimage).size
                image_ar = float(image_width) / float(im_height)
                if not simple_almost_equal(image_ar, self.scene_ar):
                    print("Warning: image aspect ratio different from scene aspect ratio."
                          "\nImage covers full scene. "
                          "\nConsider change image %s size" % showthisimage)
                self.photomarker("image")
                time_before_image = time()
                img_obj = self.picture(self.waldoimagepath + showthisimage, duration=self.image_time, pos=[0, 0, 0],
                                       scale=[self.scene_ar, 1, 1], block=False)
                if self.show_mask:
                    msk_obj = self.picture(self.waldomaskpath + usethismask, duration=self.image_time, pos=[0, 0, 0],
                                           scale=[self.scene_ar, 1, 1], color=[1, 1, 1, 0.2], block=False)

                self.wait4fixation(gaze_inlet=inlet, duration=self.fixation_time, max_duration=self.image_time,
                                   mask_array=mask_image_array)
                # inlet.flush()

                if self.show_cursor:
                    self.removeCursor()

                # wait to get the screen updated and the images to disappear
                time2wait = max(self.image_time - time() + time_before_image, 0)
                if time2wait > 0:
                    img_obj.destroy()
                    if self.show_mask:
                        msk_obj.destroy()
                self.sleep(1.0 / self.framerate)

                # wait before going to the next image
                self.sleep(uniform(self.blank_time[0], self.blank_time[1]))
                self.cursorPos = (0, 0, 0)

        """ end main loop """
        # end of experiment
        self.write(
            text="\1text\1" + self.textExperimentEnd,
            duration='space')

    def show_feedback(self, posneg):
        # presenting positive/negative feedback
        if posneg:
            file = self.feedbackposfile
        else:
            file = self.feedbacknegfile

        self.sleep(self.beforefeedbacktime + (random() * 2 - 1) * self.beforefeedbacktimedev)
        self.photomarker("feedback" + str(posneg))
        self.picture(file, duration=self.feedbacktime, scale=self.feedbacksize, color=self.feedbackcolor)

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
            text=text,
            font=self.fontFace,
            scale=self.textScale,
            fg=self.textColour,
            bg=self.textBgColour,
            wordwrap=25,
            duration=0,
            block=False)
        self.alignVertical(text, 1)

        if time == 0:
            self.waitfor("space")
        else:
            self.sleep(time)

        text.destroy()

    def alignVertical(self, object, align=1):
        # helper function for vertical alignment of text
        # 0 = top, 1 = center, 2 = bottom
        b = object.getTightBounds()
        z = [1 - b[1][2], -(b[1] + b[0])[2] * .5, -b[0][2] - 1]
        object.setZ(z[align])

    def photomarker(self, marker, position=None):
        # sending generic LSL marker
        self.marker(marker)

        # flashing coloured square to be picked up by photo sensor
        position = self.photomarkerPosition if position is None else position

        ar = base.getAspectRatio()
        sc = self.photomarkerScale

        if position == "tl":
            rect = [-ar, sc - ar, 1, 1 - sc]
        elif position == "ll":
            rect = [-ar, sc - ar, sc - 1, -1]
        elif position == "tr":
            rect = [ar - sc, ar, 1, 1 - sc]
        elif position == "lr":
            rect = [ar - sc, ar, sc - 1, -1]

        self.rectangle(
            rect=rect,
            duration=self.photomarker_time,
            color=self.photomarkerColour,
            block=False)

    def log(self, *args):
        if self.logging:
            logfile = open(self.logFile, "a")
            logfile.write("\n" + self.subject + ";" + str(time()) + ";" + ";".join(map(str, args)))
            logfile.close()

    def exit(self):
        print "Exiting..."
        exit()
