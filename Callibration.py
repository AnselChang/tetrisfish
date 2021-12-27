import pygame
import sys
import pickle
import os
import math
import time
import cv2
import PieceMasks
from TetrisUtility import *

import config as c
import PygameButton
from colors import *
import Evaluator
from Position import Position
import Analysis
from calibrate import autofindfield
from calibrate.bounds import Bounds
from calibrate.slider import HzSlider, Slider
import calibrate.image_names as im_names
import calibrate.mouse_status as mouse_status
from calibrate.error_msg import ErrorMessage
from calibrate.videodragger import VideoDragger
from enum import Enum
PygameButton.init(c.font)

images = loadImages(c.fp("Images/Callibration/{}.png"), im_names.CALLIBRATION_IMAGES)


# Image stuff
#background = images[im_names.C_BACKDROP]
background = [None] * 2
background[c.NTSC] = pygame.transform.smoothscale(images[im_names.C_NTSC], [c.SCREEN_WIDTH, c.SCREEN_HEIGHT])
background[c.PAL] = pygame.transform.smoothscale(images[im_names.C_PAL], [c.SCREEN_WIDTH, c.SCREEN_HEIGHT])

              
 # Hydrant-to-Primer scaling factor
hydrantScale = c.SCREEN_WIDTH / images[im_names.C_NTSC].get_width()
c.hydrantScale = hydrantScale



# Mapping of keys to how many frames to seek
keyshift = {pygame.K_COMMA : -1, pygame.K_PERIOD : 1, pygame.K_LEFT : -20, pygame. K_RIGHT : 20}

class ButtonIndices(Enum):
    CALLIBRATE = 0
    NEXTBOX = 1
    PLAY = 2
    RUN = 3
    RENDER = 4
    LEFT = 5
    RIGHT = 6
    LEVEL = 9
    LINES = 10
    SCORE = 11
    SAVE = 12
    LOAD = 13
    CHECK = 14
    AUTOCALIBRATE = 15
    PAL = 16

COLOR_CALIB_CONST = 150

class Calibrator:
    def __init__(self):
        self.frame = None
        self.buttons = None
        
        self.colorSlider = None
        self.zoomSlider = None
        self.hzSlider = None
        
        self.leftVideoSlider = None
        self.rightVideoSlider = None

        self.segmentred = None
        self.segmentgrey = None
        
        self.bounds = None
        self.nextBounds = None
        self.boundsManager = None

        self.vcap = None
        self.frame = None
        self.vidFrame = [0] * 3



        # video slider.  todo: move into class
        self.LEFT_FRAME = 0
        self.RIGHT_FRAME = 1
        self.SEGMENT_FRAME = 2
        self.vidFrame[self.LEFT_FRAME] = 0
        self.vidFrame[self.RIGHT_FRAME] = c.totalFrames - 100
        self.currentEnd = self.LEFT_FRAME
        self.rightVideoSlider.setAlt(False)
        self.leftVideoSlider.setAlt(True)
        self.segmentActive = False
        self.previousFrame = -1

        
        self.error = None # current error message to render
        self.video_dragger = VideoDragger()
        self.mouse_status = MouseStatus()
    
        self.init_image()
        self.init_buttons()
        self.init_sliders()
        # Get new frame from opencv
        if not c.isImage:
            self.frame = c.goToFrame(self.vcap, 0)[0]
            b = buttons.get(B_PLAY)

        
    
    def callibrate(self):
        while True:
            c.realscreen.fill([38,38,38])
            # draw backgound
            c.screen.blit(self.background[c.gamemode],[0,0])

            surf = c.displayTetrisImage(self.frame)
            self.mouse_status.start_frame_update()
            self.buttons.updatePressed(*self.mouse_status.pygame_button_handler())
            self.handle_video_buttons()
            self.handle_calibrate_buttons()
            self.handle_check_button()
            self.handle_pal_button()
            self.handle_save_button()
            self.handle_load_button()

            self.update_bounds()
            self.update_video_drag()
            
            result = self.handle_render_button()
            if result is not None:
                if len(result) == 0:
                    return None
                else: 
                    return result
            
            self.render_sliders() # note this updates some values
            self.update_video_slider_segment()
            self.render_error()
            self.render_text()
            self.buttons.display(c.screen,
                                 self.mouse_status.x,
                                 self.mouse_status.y)
            
            self.handle_pygame_events()

            c.handleWindowResize()
            
            pygame.display.update()
            pygame.time.wait(20)

    def init_image(self):
        if c.isImage:
            self.frame = cv2.imread(c.filename)
            self.frame = np.flip(self.frame,2)

            c.VIDEO_WIDTH = len(self.frame[0])
            c.VIDEO_HEIGHT = len(self.frame)
        
        else:
            self.vcap = c.getVideo()
            c.VIDEO_WIDTH = int(self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH))
            c.VIDEO_HEIGHT = int(self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            c.totalFrames = int(self.vcap.get(cv2.CAP_PROP_FRAME_COUNT))
            c.fps = self.vcap.get(cv2.CAP_PROP_FPS)
            self.frame = c.goToFrame(self.vcap, 0)[0]
        print(c.VIDEO_WIDTH, c.VIDEO_HEIGHT)
    
    def init_buttons(self):
        buttons = PygameButton.ButtonHandler()
        buttons.addImage(ButtonIndices.AUTOCALIBRATE, images[im_names.C_ABOARD], 1724, 380, hydrantScale, img2= images[im_names.C_ABOARD2],
                         tooltip = ["Uses AI to try to find your board and next box.", 
                                    "Currently only works for centered or Stencil™ boards;",
                                    "But will expand over time to be more AI"])

        buttons.addImage(ButtonIndices.CALLIBRATE, images[im_names.C_BOARD], 1724, 600, hydrantScale, img2 = images[im_names.C_BOARD2],
                         tooltip = ["Set the bounds for the tetris board. One dot",
                                    "should be centered along each mino."])
        buttons.addImage(ButtonIndices.NEXTBOX, images[im_names.C_NEXT], 2100, 600, hydrantScale, img2 = images[im_names.C_NEXT2],
                         tooltip = ["Set the bounds across the active area of the entire",
                                    "next box. Make sure four dots are symmetrically placed",
                                    "along each mino. Press 'T' for a MaxoutClub layout"])
        if not c.isImage:
            buttons.addImage(ButtonIndices.PLAY, images[im_names.C_PLAY], 134,1377, hydrantScale, img2 = images[im_names.C_PLAY2], alt = images[im_names.C_PAUSE],
                             alt2 = images[im_names.C_PAUSE2], tooltip = ["Shortcuts: , and . to move back or forward a frame", "Arrow keys to skip behind or ahead",
                                                                 "Spacebar to toggle between starting and ending frame"])
            buttons.addImage(ButtonIndices.LEFT, images[im_names.C_PREVF], 45, 1377, hydrantScale, img2 = images[im_names.C_PREVF2])
            buttons.addImage(ButtonIndices.RIGHT, images[im_names.C_NEXTF], 207, 1377, hydrantScale, img2 = images[im_names.C_NEXTF2])
    
        buttons.addImage(ButtonIndices.RENDER, images[im_names.C_RENDER], 1862, 1203, hydrantScale, img2 = images[im_names.C_RENDER2], tooltip = ["Shortcut: Enter key"])


        c1dark = images[im_names.C_CHECKMARK].copy().convert_alpha()
        addHueToSurface(c1dark, BLACK, 0.3)
        c2dark = images[im_names.C_CHECKMARK2].copy().convert_alpha()
        addHueToSurface(c2dark, BLACK, 0.3)
        buttons.addImage(ButtonIndices.CHECK, images[im_names.C_CHECKMARK], 1714, 1268, 0.3, img2 = c1dark, alt = images[im_names.C_CHECKMARK2],
                         alt2 = c2dark, tooltip = ["Depth 3 search takes longer but is more accurate.", "Depth 2 is faster, but will self-correct to depth 3 eventually."])

        buttons.get(ButtonIndices.CHECK).isAlt = True

        buttons.addImage(ButtonIndices.PAL, images[im_names.C_CHECKMARK], 1890, 30, 0.3, img2 = c1dark, alt = images[im_names.C_CHECKMARK2],
                         alt2 = c2dark, tooltip = ["PAL mode. Only configured for level 18+"])

        buttons.addInvisible(1726,880, 2480, 953, tooltip = ["The threshold for how bright the pixel must be to",
            "be considered a mino. You may need to increase",
            "this value for scuffed captures. Check especially",
            "that level 21 and 27 colors are captured properly"])

        save2 = images[im_names.C_SAVE].copy().convert_alpha()
        load2 = images[im_names.C_LOAD].copy().convert_alpha()
        addHueToSurface(save2,BLACK,0.2)
        addHueToSurface(load2,BLACK,0.2)
        load3 = images[im_names.C_LOAD].copy().convert_alpha()
        addHueToSurface(load3,BLACK,0.6)

        buttons.addImage(ButtonIndices.LOAD, images[im_names.C_LOAD], 1462, 1364, 0.063, img2 = load2, alt = load3, alt2 = load3, tooltip = ["Load callibration settings"])
        buttons.addImage(ButtonIndices.SAVE, images[im_names.C_SAVE], 1555, 1364, 0.27, img2 = save2, tooltip = ["Save callibration settings"])

        buttons.addTextBox(ButtonIndices.LEVEL, 1940, 125, 70, 50, 2, "18", tooltip = ["Level at GAME start, not", "at the render selection start"])
        buttons.addTextBox(ButtonIndices.LINES, 2410, 125, 90, 50, 3, "0")
        buttons.addTextBox(ButtonIndices.SCORE, 2330, 40, 170, 50, 7, "0")
        self.buttons = buttons

    def init_sliders(self):
        # Slider stuff
        SW = 680 # slider width
        LEFT_X = 1720
        SLIDER_SCALE = 0.6
        sliderImage = scaleImage(images[im_names.C_SLIDERF], SLIDER_SCALE)
        sliderImage2 = scaleImage(images[im_names.C_SLIDER2F], SLIDER_SCALE)
        sliderImage3 = scaleImage(images[im_names.C_SLIDER], SLIDER_SCALE)
        sliderImage4 = scaleImage(images[im_names.C_SLIDER2], SLIDER_SCALE)

        rect = pygame.Surface([30,75])
        rect2 = rect.copy()
        rect.fill(WHITE)
        rect2.fill([193,193,193])
    
        self.colorSlider = Slider(LEFT_X + 2, 875, SW + 50, c.COLOR_CALLIBRATION / COLOR_CALIB_CONST, rect, rect2, margin = 10)
        self.zoomSlider = Slider(LEFT_X, 1104, SW + 15, c.SCALAR / 4, sliderImage3, sliderImage4, margin = 10)
        self.hzSlider = HzSlider(LEFT_X + 12, 203, SW, 0, sliderImage, sliderImage2, margin = 10)
        self.hzNum = 2
        self.hzSlider.overwrite(self.hzNum)
        self.set_zoom_automatically()

        SW2 = 922
        LEFT_X2 = 497
        Y = 1377
        self.leftVideoSlider = Slider(LEFT_X2, Y, SW2, 0, scaleImage(images[im_names.C_LVIDEO],hydrantScale), scaleImage(images[im_names.C_LVIDEO2],hydrantScale),
                                    scaleImage(images[im_names.C_LVIDEORED], hydrantScale), scaleImage(images[im_names.C_LVIDEORED2], hydrantScale), margin = 10)
        self.rightVideoSlider = Slider(LEFT_X2, Y, SW2, 1, scaleImage(images[im_names.C_RVIDEO],hydrantScale), scaleImage(images[im_names.C_RVIDEO2],hydrantScale),
                                    scaleImage(images[im_names.C_RVIDEORED], hydrantScale), scaleImage(images[im_names.C_RVIDEORED2], hydrantScale), margin = 10)



        self.segmentred = scaleImage(images[im_names.C_SEGMENT], hydrantScale)
        self.segmentgrey = scaleImage(images[im_names.C_SEGMENTGREY], hydrantScale)
    
    def set_zoom_automatically(self):
        # init zoom to show full image:
        widthRatio = c.X_MAX / c.VIDEO_WIDTH
        heightRatio = c.Y_MAX / c.VIDEO_HEIGHT
        autoZoom = min(widthRatio,heightRatio, 4) # magic, the four is max zoom
        c.SCALAR = autoZoom
        self.zoomSlider.overwrite(autoZoom / 4) # lol magic
    
    def handle_video_buttons(self):
        if not c.isImage:
            self.handle_play_button()
            self.track_video() #todo: move to event loop
            self.handle_video_left_arrow()
            self.handle_video_right_arrow()

    """ video player handling functions"""
    def handle_play_button(self):
        b = self.buttons.get(ButtonIndices.PLAY)
        if b.clicked:
            b.isAlt = not b.isAlt
    
    def track_video(self, key):
        b = self.buttons.get(ButtonIndices.PLAY)
        if key is not None:
            b.isAlt = False
            self.frame, self.vidFrame[currentEnd] = c.goToFrame(self.vcap, self.vidFrame[currentEnd] + self.keyshift[key])
            assert(type(self.frame) == np.ndarray)
    
    def handle_video_right_arrow(self):
        b = self.buttons.get(ButtonIndices.PLAY)
        if (b.isAlt or self.buttons.get(ButtonIndices.RIGHT).clicked and self.vidFrame[currentEnd] < c.totalFrames - 100):
            seekDistance = 2 if b.isAlt else 1
            self.frame, self.vidFrame[currentEnd] = c.goToFrame(self.vcap, self.vidFrame[currentEnd] + seekDistance)
            assert(type(self.frame) == np.ndarray)

    def handle_video_left_arrow(self):
        if buttons.get(ButtonIndices.LEFT).clicked and vidFrame[currentEnd] > 0:
            # load previous frame
            self.frame, self.vidFrame[currentEnd] = c.goToFrame(self.vcap, self.vidFrame[currentEnd] - 1)
            assert(type(frame) == np.ndarray)

    def handle_calibrate_buttons(self):
        self.handle_auto_calibrate_button()
        self.handle_calibrate_field_button()
        self.handle_calibrate_next_button()

    def handle_auto_calibrate_button(self):
        if not self.buttons.get(ButtonIndices.AUTOCALIBRATE).clicked:
            return
        #todo return multiple regions if possible
        pixels, suggested = autofindfield.get_board(self.frame) 
        board_pixels = pixels or (0,0,c.VIDEO_WIDTH,c.VIDEO_HEIGHT)
        self.bounds = Bounds(False, config=c)
        self.bounds.setRect(board_pixels)
        if pixels: # successfully found board
            pixels, preview_layout = autofindfield.get_next_box(self.frame, pixels, suggested)
            if pixels is not None:
                self.nextBounds = Bounds(True, config=c)
                self.nextBounds.setRect(pixels)
                self.nextBounds.setSubRect(preview_layout.inner_box)
                self.nextBounds.sub_rect_name = preview_layout.name
        for bounds in [self.nextBounds, self.bounds]:
            if bounds is not None:
                bounds.set()
            
    def handle_calibrate_field_button(self):
        if self.buttons.get(ButtonIndices.CALLIBRATE).clicked:
            self.bounds = Bounds(False, config=c)
            if self.nextBounds is not None:
                self.nextBounds.set()
    
    def handle_calibrate_next_button(self):
        if self.buttons.get(ButtonIndices.NEXTBOX).clicked:
            self.nextBounds = Bounds(True, config=c)
            if self.bounds is not None:
                self.bounds.set()
    
    def handle_check_button(self):
        b = self.buttons.get(ButtonIndices.CHECK)
        if b.clicked:
            b.isAlt = not b.isAlt
            c.isDepth3 = b.isAlt
            c.isEvalDepth3 = b.isAlt
    
    def handle_pal_button(self):
        b = self.buttons.get(ButtonIndices.PAL)
        if b.clicked:
            b.isAlt = not b.isAlt
            c.gamemode = c.PAL if b.isAlt else c.NTSC

    def bounds_valid(self):
        for item in [self.bounds,self.nextBounds]:
            if item is None:
                return False
            if item.notSet:
                return False
        return True

    def handle_render_button(self, force): #force == enter key
        """
        Returns None (error), 
        [] for image, and 
        [list of data] for video
        """
        if not self.buttons.get(ButtonIndices.RENDER).clicked and not force: 
            return

        c.startLevel = self.get_button_value(ButtonIndices.LEVEL)

        if c.gamemode == c.PAL and not self.get_button_value(ButtonIndices.LEVEL) in [18,19]:
            self.error = ErrorMessage("Only level 18 and 19 are supported for PAL.")
            return
        # If not callibrated, do not allow render
        if not self.bounds_valid():
            self.error = ErrorMessage("You must set bounds for the board and next box.")
            return
        
        if not c.isImage:
            frame, _ = c.goToFrame(self.vcap, self.vidFrame[self.LEFT_FRAME])
                
        board = self.bounds.getMinos(frame)
        mask = extractCurrentPiece(board)
        currPiece = getPieceMaskType(mask)
        preview = self.nextBounds.getMinos(frame)
        if currPiece is None:
            self.error = ErrorMessage("The current piece must be near the top ",
                                      "with all four minos fully visible.")
            return

        if getNextBox(preview) is None:
            self.error = ErrorMessage("The next box must be callibrated so that",
                                      "four dots are inside each mino.")
            return
        
        print2d(board)
        print2d(preview)

                    
        if c.isImage: # We directly call analysis on the single frame

            print("Rendering...")
                        
            board -= mask # remove current piece from board to get pure board state
            print2d(board)
            minosNext = nextBounds.getMinos(nparray = frame)
            nextPiece = getNextBox(minosNext)
            c.hzString = PieceMasks.timeline[self.hzNum][c.gamemode]
            pos = Position(board, currPiece, nextPiece, 
                            level = self.get_button_value(ButtonIndices.LEVEL),
                            lines = self.get_button_value(ButtonIndices.LINES), 
                            score = self.get_button_value(ButtonIndices.SCORE))
            Analysis.analyze([pos], timelineNum[c.gamemode][hzNum])

            return []

                        
        else:
            # When everything done, release the capture
            self.vcap.release()

            # Exit callibration, initiate rendering with returned
            # parameters
            print("Hz num: ", PieceMasks.timelineNum[c.gamemode][self.hzNum])
            c.hzString = PieceMasks.timeline[hzNum][c.gamemode]
            return [self.vidFrame[self.LEFT_FRAME], self.vidFrame[self.RIGHT_FRAME], 
                    self.bounds, self.nextBounds, 
                    self.get_button_value(ButtonIndices.LEVEL),
                    self.get_button_value(ButtonIndices.LINES),
                    self.get_button_value(ButtonIndices.SCORE), 
                    PieceMasks.timelineNum[c.gamemode][self.hzNum]]
    
    
    def get_button_value(self, index):
        return self.buttons.get(index).value()
    
    def clear_bounds(self):
        self.bounds = None
    def clear_nextBounds(self):
        self.nextBounds = None
    def clear_boundsManager(self):
        self.boundsManager = None

    def update_bounds(self):
        for bound, deassign in [(self.bounds, self.clear_bounds),
                                (self.nextBounds, self.clear_nextBounds),
                                (self.boundsManager,self.clear_boundsManager)]:
        
            if bound is not None:
                delete = bounds.updateMouse(*self.mouse_status.bounds_handler())
                if delete:
                    deassign()
                else:
                    bound.displayBounds(c.screen, nparray = self.frame)
    
    def handle_bounds_click(self):
        for item in [boundsManager, bounds, nextBounds]:
            if item is not None:
                item.click(self.mouse_status.x,self.mouse_status.y)
        
    def update_video_drag(self):
        self.video_dragger.update(self.mouse_status)
        
    def handle_video_drag_click(self):
        """
        Only called when we get an event from clicking
        """
        mx, my = self.mouse_status.x, self.mouse_status.y
        if not self.mouse_status.out_of_bounds():
            b = (self.bounds is None or not self.bounds.mouseNearDot(mx, my))
            nb = (self.nextBounds is None or not self.nextBounds.mouseNearDot(mx, my))
                
            if b and nb:
                self.video_dragger.start(mx,my,c.VIDEO_X,c.VIDEO_Y)
                   
    def handle_left_click_event(self):
        """mouse button left click event"""
        self.handle_video_drag_click()
        self.handle_bounds_click()

    def handle_left_release_event(self):
        """mouse button left release event"""
        self.video_dragger.stop()
    
    def handle_save_button(self):
        # Pickle callibration settings into file
        # Save hz, bounds, nextBounds, color callibration, zoom
        if self.buttons.get(ButtonIndices.SAVE).clicked:

            # tetris board
            if self.bounds == None:
                bData = None
            else:
                bData = self.bounds.to_json()

            # next box
            if self.nextBounds == None:
                nData = None
            else:
                nData = self.nextBounds.to_json()

            data = [hzNum, bData, nData, c.COLOR_CALLIBRATION, c.SCALAR]
            pickle.dump(data, open("callibration_preset.p", "wb"))

            print("Saved preset", data)
            self.error = ErrorMessage("Calibration preset saved", WHITE)
            
    def handle_load_button(self):

        bload = self.buttons.get(ButtonIndices.LOAD)
        bload.isAlt = not os.path.isfile("callibration_preset.p")
        # return if no file, or if we didnt click
        if bload.isAlt  or not bload.clicked:
            return 
            
        data = pickle.load(open("callibration_preset.p", "rb"))

        self.hzNum = data[0]
        c.COLOR_CALLIBRATION = data[3]
        c.SCALAR = data[4]

        colorSlider.overwrite(c.COLOR_CALLIBRATION / COLOR_CALIB_CONST)
        zoomSlider.overwrite(c.SCALAR / 4)
        hzSlider.overwrite(self.hzNum)

            
        if data[1] is None:
            self.bounds = None
        else:
            self.bounds = Bounds(data[1], config=c)
            self.bounds.notSet = False

        if data[2] is None:
            self.nextBounds = None
        else:
            self.nextBounds = Bounds(data[2], config=c)
            self.nextBounds.notSet = False
            
        print("loaded preset", data)
        self.error = ErrorMessage("Callibration preset loaded.", WHITE)

    def render_sliders(self):
        slider_args = self.mouse_status.slider_arguments()
        # Draw sliders
        c.COLOR_CALLIBRATION = COLOR_CALIB_CONST * self.colorSlider.tick(c.screen, c.COLOR_CALLIBRATION / COLOR_CALIB_CONST, *slider_args)
        c.SCALAR = max(0.1,4 * self.zoomSlider.tick(c.screen, c.SCALAR / 4, *slider_args))
        self.hzNum = hzSlider.tick(c.screen, hzNum, *slider_args)
        c.screen.blit(c.font.render(str(int(c.COLOR_CALLIBRATION)), True, WHITE), [1650, 900])
        

        # Draw video bounds sliders
        if not c.isImage:
            slider_args = slider_args + [True]
            self.vidFrame[self.RIGHT_FRAME] = self.rightVideoSlider.tick(c.screen, self.vidFrame[self.RIGHT_FRAME] / (c.totalFrames - 1), *slider_args)
            self.vidFrame[self.RIGHT_FRAME] = clamp(int(self.vidFrame[self.RIGHT_FRAME] * c.totalFrames), 0, c.totalFrames - 100)
            slider_args = [slider_args[0] and not rightVideoSlider.active] + slider_args[1:]
            self.vidFrame[self.LEFT_FRAME] = self.leftVideoSlider.tick(c.screen, self.vidFrame[self.LEFT_FRAME] / (c.totalFrames - 1), *slider_args)
            self.vidFrame[self.LEFT_FRAME] = clamp(int(self.vidFrame[self.LEFT_FRAME] * c.totalFrames),0,c.totalFrames - 100)

        # Update frame from video sliders
        if self.rightVideoSlider.active:
            self.rightVideoSlider.setAlt(True)
            self.leftVideoSlider.setAlt(False)
            self.segmentActive = False
            self.currentEnd = self.RIGHT_FRAME
            self.frame, self.vidFrame[self.currentEnd] = c.goToFrame(self.vcap, self.vidFrame[self.currentEnd])
        elif self.leftVideoSlider.active:
            self.currentEnd = self.LEFT_FRAME
            self.rightVideoSlider.setAlt(False)
            self.leftVideoSlider.setAlt(True)
            self.segmentActive = False
            self.frame, self.vidFrame[self.currentEnd] = c.goToFrame(self.vcap, self.vidFrame[self.currentEnd])


    def update_video_slider_segment(self):
        """ the red (or grey) segment that follows the mouse """
        SW2 = 922
        LEFT_X2 = 497
        Y = 1377
        mx , my = self.mouse_status.x, self.mouse_status.y
        
        inVideoSlider = (mx > LEFT_X2 - 20 and mx < LEFT_X2 + SW2 + 20 and my > Y - 30 and my < Y + 60)
        # calculate whether we are active.

        if not self.leftVideoSlider.active and not rightVideoSlider.active and inVideoSlider and not c.isImage:
            if self.mouse_status.left_pressed:
                self.segmentActive = True
                self.rightVideoSlider.setAlt(False)
                self.leftVideoSlider.setAlt(False)
                self.currentEnd = self.SEGMENT_FRAME
                self.vidFrame[self.SEGMENT_FRAME] = clamp((c.totalFrames) * (mx - LEFT_X2) / SW2, 0, c.totalFrames - 100)
                self.frame, self.vidFrame[self.currentEnd] = c.goToFrame(self.vcap, self.vidFrame[self.currentEnd])
            elif not leftVideoSlider.isHovering(mx,my) and not rightVideoSlider.isHovering(mx,my):
                c.screen.blit(self.segmentgrey, [mx - 10, Y])

        if self.segmentActive:
            c.screen.blit(segmentred, [LEFT_X2 - 5 + SW2 * self.vidFrame[self.SEGMENT_FRAME] / (c.totalFrames - 1) , Y])

    def handle_space_release(self):
        """changes current end point of video"""
        if c.isImage:
            return

        if self.currentEnd == self.LEFT_FRAME:
            self.currentEnd = self.RIGHT_FRAME
            self.rightVideoSlider.setAlt(True)
            self.leftVideoSlider.setAlt(False)
            self.segmentActive = False
        else:
            self.currentEnd = self.LEFT_FRAME
            self.rightVideoSlider.setAlt(False)
            self.leftVideoSlider.setAlt(True)
            self.segmentActive = False
        self.frame, self.vidFrame[self.currentEnd] = c.goToFrame(self.vcap, self.vidFrame[self.currentEnd])

        assert(type(frame) == np.ndarray)

    def render_error(self):
        # Draw error message
        if self.error is not None:
            if error.expired():
                error = None
            else:
                text = c.font2.render(error.text, True, error.color)
                c.screen.blit(text, [1670,1380])
    def render_text(self):
        # Draw timestamp
        if c.isImage:
            text = c.font.render("[No video controls]", True, WHITE)
            c.screen.blit(text, [80, 1373])
        else:
            text = c.font.render(c.timestamp(vidFrame[currentEnd]), True, WHITE)
            c.screen.blit(text, [300, 1383])

        # Draw Level/Lines/Score text
        c.screen.blit(c.fontbold.render("PAL?", True, WHITE), [1770, 40])
        c.screen.blit(c.fontbold.render("Start Level:", True, WHITE), [1700, 125])
        c.screen.blit(c.fontbold.render("Current Lines:", True, WHITE), [2100, 125])
        c.screen.blit(c.fontbold.render("Current Score:", True, WHITE), [2050, 40])

        c.screen.blit(c.fontbold.render("Deep?", True, WHITE), [1700, 1215])

    def handle_pygame_event(self, event):
        if event.type == pygame.QUIT:
            if not c.isImage:
                self.vcap.release()
            pygame.display.quit()
            sys.exit()

        elif event.type == pygame.VIDEORESIZE:
            c.realscreen = pygame.display.set_mode(event.size, 
                                                   (pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_status.start_press = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_status.end_press = True
        elif event.type == pygame.KEYDOWN:
            isTextBoxScroll = self.buttons.updateTextboxes(event.key)
            if isTextBoxScroll:
                return
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_COMMA, pygame.K_PERIOD]:
                self.track_video(event.key)
            elif event.key == pygame.K_RETURN:
                self.handle_render_button(force=True)
            elif event.key == pygame.K_t:
                # toggle next box subrectangle between
                # maxoutclub/regular/precise
                if self.nextBounds is not None:
                    self.nextBounds.cycle_sub_rect()
                    print ("Toggled bounds to :", self.nextBounds.sub_rect_name)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                self.handle_space_release()

    def handle_pygame_events(self):
        key = None
        enterKey = False        
        self.mouse_status.pre_update_event_loop()
        for event in pygame.event.get():
            self.handle_pygame_event(event)
