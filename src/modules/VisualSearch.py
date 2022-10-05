#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

"""
@authors    TSE, AGC, NVJ
@org        ZLS
@date       2022-09-27
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
from math import floor
from pylslx import StreamInlet, resolve_stream
from collections import deque
from PIL import Image
import numpy as np
import pandas as pd


# from pylsl import StreamInfo, StreamOutlet,


def simple_almost_equal(a, b, dec=3):
    return (a == b or
            int(floor(a * 10 ** dec)) == int(floor(b * 10 ** dec)))


class Main(LatentModule):
    def __init__(self):
        LatentModule.__init__(self)

        # Scene size
        self.scene_sx = float(base.win.getXSize())
        self.scene_sy = float(base.win.getYSize())
        self.scene_ar = float(self.scene_sx / self.scene_sy)

        self.show_cursor = True
        self.show_mask = True
        self.fill_nans = True
        self.fill_2much_ratio = 2

        # read images for stimuli
        self.waldopath = "./media/waldo/"  # media path
        self.waldomasksfolder = "masks/"  # mask folder
        self.waldoimagesfolder = "images/"  # images folder

        # Waldo/Wally # Wenda # White beard # Odlaw
        self.waldotarget = ["ch1", "ch2", "ch3", "ch4"]
        # random order of targets
        shuffle(self.waldotarget)
        self.blocks = 5  # number of blocks

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
        self.crossColour = (.5, .5, .5, 1)  # colour of the crosshair
        self.crossScale = 0.15  # size of the crosshair

        self.circle_file = "./media/circle.png"
        self.circleTime = [0.5, 0.9]  # duration range in seconds that the crosshair is visible before each block
        self.circleScale = 0.05  # size of the circle
        self.circleColour = (.5, .5, .5, 1)  # colour of the crosshair
        self.margin = 0.8
        self.circleScale = 0.05  # size of the circle

        self.gaze_framerate = 600  # de expected frame rate (in Hz) of the gaze data
        self.fadeTime = 0.5  # time that sparkles/tasks take to fade in/out, in seconds
        # setting fade length in frames
        self.fadeFrames = int(self.fadeTime / self._frametime)

        self.currenttrial = 0  # main index for trials

        self.cursor = None
        self.cursorAlpha = 0.4
        self.cursorScale = 0.05
        self.cursorPos = (0, 0, 0)
        self.cursorColor = (0.92, 0.04, 0.56)

        self.circleGraphics = None
        self.crossGraphics = None

    def screen2scene(self, x, y):
        return (2 * x / self.scene_sx - 1) * self.scene_ar, -2 * y / self.scene_sy + 1

    def screen2image(self, x, y, im_width, im_height):
        x = int(float(x) / self.scene_sx * im_width)
        y = int(float(y) / self.scene_sy * im_height)

        # # bound the indices to [0, im_width-1] and [0, im_height - 1]
        # x = 0 if x < 0 else x
        # x = im_width - 1 if x >= im_width else x
        # y = 0 if y < 0 else y
        # y = im_height - 1 if y >= im_height else y

        return x, y

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
        # Create the graphical object
        self.circleGraphics = self._engine.direct.gui.OnscreenImage.OnscreenImage(
            image='circle.png',
            scale=self.circleScale,
            pos=[pos[0], 0, pos[1]],
            color=(self.circleColour[0], self.circleColour[1], self.circleColour[2], 0))
        self.circleGraphics.setTransparency(1)

        # fading circle in
        for i in range(self.fadeFrames - 1):
            self.circleGraphics.setColor((self.circleColour[0],
                                          self.circleColour[1],
                                          self.circleColour[2],
                                          self.circleColour[3] * float(i) / self.fadeFrames))
            self.sleep(self._frametime)
        # make sure it is visible at the end
        self.circleGraphics.setColor((self.circleColour[0], self.circleColour[1],
                                      self.circleColour[2], self.circleColour[3]))

    def circleOff(self):
        # fading circle out
        for i in range(self.fadeFrames):
            self.circleGraphics.setColor((self.circleColour[0],
                                          self.circleColour[1],
                                          self.circleColour[2],
                                          self.circleColour[3] - self.circleColour[3] * float(i) / self.fadeFrames))
            self.sleep(self._frametime)

        self.circleGraphics.destroy()

    def crossOn(self, pos=(0, 0)):
        self.crossGraphics = self._engine.direct.gui.OnscreenImage.OnscreenImage(
            image='cross.png',
            pos=[pos[0], 0, pos[1]],
            scale=self.crossScale,
            color=(self.crossColour[0], self.crossColour[1], self.crossColour[2], 0))
        self.crossGraphics.setTransparency(1)

        # fading cross in
        for i in range(self.fadeFrames - 1):
            self.crossGraphics.setColor((self.crossColour[0],
                                         self.crossColour[1],
                                         self.crossColour[2],
                                         self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(self._frametime)

        self.crossGraphics.setColor((self.crossColour[0], self.crossColour[1],
                                     self.crossColour[2], self.crossColour[3]))

    def crossOff(self):
        # fading cross out
        for i in range(self.fadeFrames):
            self.crossGraphics.setColor((self.crossColour[0], self.crossColour[1], self.crossColour[2],
                                         self.crossColour[3] - self.crossColour[3] * float(i) / self.fadeFrames))
            self.sleep(self._frametime)

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
        self.cursor.setColor((self.cursorColor[0], self.cursorColor[1], self.cursorColor[2], self.cursorAlpha))

    def removeCursor(self):
        # destroy the cursor
        if self.cursor is not None:
            self.cursor.destroy()
            self.cursor = None

    def wait4fixation(self, gaze_inlet, fix_duration, max_duration, fix_threshold=0.9, check_every=0.1,
                      mask_array=None, location=(0, 0), radius=0.05, scene_coord=True):
        fix_frames = self.gaze_framerate * fix_duration
        deq = deque(maxlen=fix_frames)
        gaze_inlet.flush()
        start_time = time()
        while True:
            # check if max duration has passed
            if time() - start_time >= max_duration:
                break
            # sleep enough to allow game to update screen
            self.sleep(0.1 * self._frametime)

            # get next available samples
            eg_sample, eg_timestamp = gaze_inlet.pull_chunk(max_samples=fix_frames)
            # print("pulled #: %d \n" % len(eg_sample), end="")
            # if there's nothing yet then try one more time
            if len(eg_sample) == 0:
                continue

            # show the cursor if required
            if self.show_cursor:
                # calculate the current gaze location
                if not np.isnan(eg_sample[-1]).any():
                    # Ignore nan and go further
                    curr_gaze = self.screen2scene((eg_sample[-1][0] + eg_sample[-1][2]) / 2,
                                                  (eg_sample[-1][1] + eg_sample[-1][3]) / 2)
                    # show the current gaze location if required
                    # print ('Position {} \r'.format((curr_gaze[0], 0, curr_gaze[1])))
                    self.showCursor((curr_gaze[0], 0, curr_gaze[1]))

            # check if enough gaze was on target,
            # namely more than 90% of the fixation time was on or around the target (a white mask pixel)
            skip = int(check_every * fix_frames)  # process in chunks of 10% to release the burden
            for i, gs in enumerate(eg_sample):
                gs_tr = (float('NaN'), float('NaN'))
                if not np.isnan(gs).any():
                    if mask_array is not None:
                        gs_tr = self.screen2image((gs[0] + gs[2]) / 2, (gs[1] + gs[3]) / 2,
                                                  mask_array.shape[1], mask_array.shape[0])
                    elif scene_coord:
                        gs_tr = self.screen2scene((gs[0] + gs[2]) / 2, (gs[1] + gs[3]) / 2)
                    else:
                        gs_tr = ((gs[0] + gs[2]) / 2, (gs[1] + gs[3]) / 2)

                # add a new sample
                deq.append(gs_tr)

                # skip until next chunk
                if skip != 0 and i % skip != 0:
                    continue

                # is there is enough data then test for fixation
                if len(deq) == fix_frames:
                    # get all data
                    data = [x for x in deq]
                    # screen/manage the nans if required
                    if self.fill_nans:
                        if np.isnan(data).any():
                            # try to bridge the gaps
                            data = pd.DataFrame(data). \
                                fillna(method='ffill', limit=fix_frames // self.fill_2much_ratio). \
                                fillna(method="bfill", limit=fix_frames // self.fill_2much_ratio).to_numpy()

                    # print("after nan #: %d" % len(data), "\r", end='')
                    # get all non nans from deq
                    data = np.array([x for x in data if not np.isnan(x).any()])

                    # if nothing remained then get more data
                    if len(data) == 0:
                        continue

                    if mask_array is not None:
                        # print(sum(mask_array[im_coord[:, 1], im_coord[:, 0]]), " / ", limit * fix_frames)
                        if self.fill_nans:  # if nans were screened than the data type is float
                            data = data.astype(int)

                        if sum(mask_array[data[:, 1], data[:, 0]]) > fix_threshold * fix_frames:
                            print("Fixation found, going to the next task")
                            self.marker("fixation")
                            return True
                    else:
                        dists = np.linalg.norm(data - location, axis=1)
                        # print(np.sum(dists < radius), " / ", limit * fix_frames)
                        if np.sum(dists < radius) > fix_threshold * fix_frames:
                            print("Fixation found, going to the next task")
                            self.marker("fixation")
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
        for block in range(len(self.waldotarget)):

            # construct path to images and masks
            self.waldoimagepath = self.waldopath + self.waldotarget[block] + "/" + self.waldoimagesfolder
            self.waldomaskpath = self.waldopath + self.waldotarget[block] + "/" + self.waldomasksfolder

            # read all images from  target character
            self.waldoimages = listdir(self.waldoimagepath)  # read available images
            shuffle(self.waldoimages)  # shuffle images inplace

            ntrialperblock = int(floor(len(self.waldoimages) / self.blocks))  # number of images in a block
            trials = int(ntrialperblock * self.blocks)  # total number of trials

            # which target?
            thistarget = self.waldotarget[block]  # target in this block
            print(thistarget)
            print(trials)

            for trial in range(trials):

                if trial % ntrialperblock == 0:  # number of trials divided by trials per block (zero every block)
                    # self-paced break
                    self.waitForUser()
                    self.sleep(1)

                showthisimage = self.waldoimages[trial]  # indicate which image to show
                usethismask = showthisimage[0:len(showthisimage) - 4] + '_mask.png'  # corresponding mask

                print(showthisimage)
                print(usethismask)

                # log image
                self.log(block + 1, trial + 1, showthisimage)

                # ##########################
                # run next trial
                # ##########################
                # Show the cross in the middle of the screen where the target will show up
                self.marker("cross")
                self.crossOn(pos=[0, 0])
                self.sleep(uniform(self.crossTime[0], self.crossTime[1]))
                self.crossOff()

                # show the target character - first show a flashing rectangle and send a marker to LSL
                self.marker(self.waldotarget[block])
                self.photomarker("target")
                self.picture(self.waldopath + thistarget + "/" + thistarget + '_b.png',
                             duration=self.target_time, pos=[0, 0, 0], scale=[0.126, 1, 0.2],
                             color=self.photomarkerColour, block=True)

                # Show a circle in a random position and wait until the user has fixated it
                pos = [uniform(-self.margin * self.scene_ar, self.margin * self.scene_ar),
                       uniform(-self.margin, self.margin)]
                self.marker("dot")
                self.circleOn(pos=pos)
                bff = time()
                self.wait4fixation(gaze_inlet=inlet,
                                   fix_duration=self.fixation_time, max_duration=self.image_time,
                                   location=pos, scene_coord=True, radius=.15)

                print("duration until fixation: ", time() - bff)
                self.circleOff()
                if self.show_cursor:
                    self.removeCursor()

                # continue
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
                                       scale=[self.scene_ar, 1, 1], color=[1, 1, 1, 1], block=False)
                if self.show_mask:
                    msk_obj = self.picture(self.waldomaskpath + usethismask, duration=self.image_time, pos=[0, 0, 0],
                                           scale=[self.scene_ar, 1, 1], color=[1, 1, 1, 0.2], block=False)
                bff = time()
                self.wait4fixation(gaze_inlet=inlet, fix_duration=self.fixation_time, max_duration=self.image_time,
                                   mask_array=mask_image_array)
                print("Duration until fixation: ", time() - bff)

                if self.show_cursor:
                    self.removeCursor()

                # wait to get the screen updated and the images to disappear
                time2wait = max(self.image_time - time() + time_before_image, 0)
                if time2wait > 0:
                    img_obj.destroy()
                    if self.show_mask:
                        msk_obj.destroy()
                # self.sleep(1.0 / self.game_framerate)

                # wait before going to the next image
                self.marker("blank")
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

        ar = self.scene_ar
        sc = self.photomarkerScale

        rect = [0, 0, 0, 0]
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
        print("Exiting...")
        exit()
