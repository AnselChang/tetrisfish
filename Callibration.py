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
from calibrate.bounds import Bounds, BoundsPicker
from calibrate.slider import HzSlider, Slider
import calibrate.image_names as im_names
from calibrate.mouse_status import MouseStatus
from calibrate.error_msg import ErrorMessage
from calibrate.videodragger import VideoDragger
from calibrate.videoslider import VideoSlider
from enum import Enum
PygameButton.init(c.font)

images = loadImages(c.fp("Images/Callibration/{}.png"), im_names.CALLIBRATION_IMAGES)


# Image stuff
#background = images[im_names.C_BACKDROP]
BACKGROUND_IMAGE = [None] * 2
BACKGROUND_IMAGE[c.NTSC] = pygame.transform.smoothscale(images[im_names.C_NTSC], [c.SCREEN_WIDTH, c.SCREEN_HEIGHT])
BACKGROUND_IMAGE[c.PAL] = pygame.transform.smoothscale(images[im_names.C_PAL], [c.SCREEN_WIDTH, c.SCREEN_HEIGHT])

              
 # Hydrant-to-Primer scaling factor
HYDRANT_SCALE = c.SCREEN_WIDTH / images[im_names.C_NTSC].get_width()
c.hydrantScale = HYDRANT_SCALE



# Mapping of keys to how many frames to seek
SCRUB_KEYSHIFT = {pygame.K_COMMA : -1, pygame.K_PERIOD : 1, pygame.K_LEFT : -20, pygame. K_RIGHT : 20}

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
        self.buttons = None
        
        self.colorSlider = None
        self.zoomSlider = None
        self.hzSlider = None

        self.bounds = None #field bounds
        self.nextBounds = None #next box bounds
        self.boundsManager = None #multiple bound renderer

        self.vcap = None # opencv frame grabber
        self.frame = None # the frame to render

        self.init_image()
        self.init_buttons()
        self.init_sliders()

        slider_components = self.init_video_sliders(VideoSlider.DEFAULT_SHAPE)
        self.video_slider = VideoSlider(c, slider_components, 
                            VideoSlider.DEFAULT_SHAPE, self.vcap)

        
        self.error = None # current error message to render
        self.ai_error = None # current error message for AI
        self.video_dragger = VideoDragger()
        self.mouse_status = MouseStatus()

        self.enterPressed = False

    def reset(self):
        
        #self.init_image()
        
        c.reset()
        
        self.video_slider.go_to_active_frame()

    def exit(self):
        
        self.vcap.release()
    
        
    def callibrate(self):
        c.isAnalysis = False
        while True:
            self.mouse_status.start_frame_update()
            self.buttons.updatePressed(*self.mouse_status.pygame_button_handler())
            self.handle_video_buttons()
            self.handle_calibrate_buttons()
            self.handle_check_button()
            self.handle_pal_button()
            self.handle_save_button()
            self.handle_load_button()
            self.handle_bounds()
            self.update_video_drag()
            

            result = self.handle_render_button(force = self.enterPressed)
            if result is not None:
                if len(result) == 0:
                    return None
                else: 
                    return result
            
            # rendering time. Note that order matters.
            c.realscreen.fill([38,38,38])
            c.displayTetrisImage(self.frame)
            self.render_bounds() # this can blit into the ui area
            c.screen.blit(BACKGROUND_IMAGE[c.gamemode],[0,0])
            
            self.update_video_sliders() #renders and calcuates at same time.
            self.render_sliders() # note this updates some values
            self.render_error()
            self.render_text()
            self.buttons.display(c.screen,
                                 self.mouse_status.x,
                                 self.mouse_status.y)
            
            result = self.handle_pygame_events()
            if type(result) == str: # filename
                return result

            c.drawWindow()
            
            pygame.display.update()
            pygame.time.wait(20)

    def update_new_footage(self):

        # When new footage is dragged onto calibration screen
        
        self.init_image()
        self.video_slider.vcap = self.vcap # vcap was passed by reference to video_slider but I for some reason vcap gets reassigned in init_image
        self.set_zoom_automatically() # zoom is different for different resolution
        
        # bounds may be different for new video resolution, so update
        if self.bounds is not None:
            self.bounds.updateConversions()
        if self.nextBounds is not None:
            self.nextBounds.updateConversions()

        slider_components = self.init_video_sliders(VideoSlider.DEFAULT_SHAPE)
        self.video_slider = VideoSlider(c, slider_components, 
                            VideoSlider.DEFAULT_SHAPE, self.vcap)

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
        print(c.VIDEO_WIDTH, c.VIDEO_HEIGHT, c.totalFrames, c.fps)
        print("vcap initialized: ", self.vcap)
    
    def init_buttons(self):
        buttons = PygameButton.ButtonHandler()
        buttons.addImage(ButtonIndices.AUTOCALIBRATE, images[im_names.C_ABOARD], 1724, 380, HYDRANT_SCALE, img2= images[im_names.C_ABOARD2],
                         tooltip = ["Uses AI to try to find your board and next box.",
                                    "Works better on frames with near-empty boards.",
                                    "Auto next-box does not work well with longbars.",
                                    "Has good compatibility with  Standard, MaxoutClub and Stencil™ boards"])

        buttons.addImage(ButtonIndices.CALLIBRATE, images[im_names.C_BOARD], 1724, 600, HYDRANT_SCALE, img2 = images[im_names.C_BOARD2],
                         tooltip = ["Set the bounds for the tetris board. One dot",
                                    "should be centered along each mino.",
                                    "Press 'B' to switch inner bounds"])

        buttons.addImage(ButtonIndices.NEXTBOX, images[im_names.C_NEXT], 2100, 600, HYDRANT_SCALE, img2 = images[im_names.C_NEXT2],
                         tooltip = ["Set the bounds across the active area of the entire",
                                    "next box. Make sure four dots are symmetrically placed",
                                    "along each mino. Press 'T' to switch inner bounds"])
        if not c.isImage:
            buttons.addImage(ButtonIndices.PLAY, images[im_names.C_PLAY], 134,1377, HYDRANT_SCALE, img2 = images[im_names.C_PLAY2], alt = images[im_names.C_PAUSE],
                             alt2 = images[im_names.C_PAUSE2], tooltip = ["Shortcuts: , and . to move back or forward a frame", "Arrow keys to skip behind or ahead",
                                                                 "Spacebar to toggle between starting and ending frame"])
            buttons.addImage(ButtonIndices.LEFT, images[im_names.C_PREVF], 45, 1377, HYDRANT_SCALE, img2 = images[im_names.C_PREVF2])
            buttons.addImage(ButtonIndices.RIGHT, images[im_names.C_NEXTF], 207, 1377, HYDRANT_SCALE, img2 = images[im_names.C_NEXTF2])
    
        buttons.addImage(ButtonIndices.RENDER, images[im_names.C_RENDER], 1862, 1203, HYDRANT_SCALE, img2 = images[im_names.C_RENDER2], tooltip = ["Shortcut: Enter key"])


        c1dark = images[im_names.C_CHECKMARK].copy().convert_alpha()
        addHueToSurface(c1dark, BLACK, 0.3)
        c2dark = images[im_names.C_CHECKMARK2].copy().convert_alpha()
        addHueToSurface(c2dark, BLACK, 0.3)
        buttons.addImage(ButtonIndices.CHECK, images[im_names.C_CHECKMARK], 1714, 1268, 0.3, img2 = c1dark, alt = images[im_names.C_CHECKMARK2],
                         alt2 = c2dark, tooltip = ["Depth 3 search takes longer but is more accurate.", "Depth 2 is faster, but will self-correct to depth 3 eventually."])

        buttons.get(ButtonIndices.CHECK).isAlt = True

        buttons.addImage(ButtonIndices.PAL, images[im_names.C_CHECKMARK], 1890, 30, 0.3, img2 = c1dark, alt = images[im_names.C_CHECKMARK2],
                         alt2 = c2dark, tooltip = ["PAL mode"])

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

        
    def init_video_sliders(self, shape):
        x, y, width = shape
        leftSlider = Slider(x, y, width, 0, 
                            scaleImage(images[im_names.C_LVIDEO],HYDRANT_SCALE), 
                            scaleImage(images[im_names.C_LVIDEO2],HYDRANT_SCALE),
                            scaleImage(images[im_names.C_LVIDEORED], HYDRANT_SCALE), 
                            scaleImage(images[im_names.C_LVIDEORED2], HYDRANT_SCALE), 
                            margin = 10)
        rightSlider = Slider(x, y, width, 1, 
                            scaleImage(images[im_names.C_RVIDEO], HYDRANT_SCALE), 
                            scaleImage(images[im_names.C_RVIDEO2], HYDRANT_SCALE),    
                            scaleImage(images[im_names.C_RVIDEORED], HYDRANT_SCALE), 
                            scaleImage(images[im_names.C_RVIDEORED2], HYDRANT_SCALE), 
                            margin = 10)
        redSegment = scaleImage(images[im_names.C_SEGMENT], HYDRANT_SCALE)
        greySegment = scaleImage(images[im_names.C_SEGMENTGREY], HYDRANT_SCALE)
        return (leftSlider, rightSlider, redSegment, greySegment)
    
    def set_zoom_automatically(self):
        # init zoom to show full image:
        widthRatio = c.X_MAX / float(c.VIDEO_WIDTH)
        heightRatio = c.Y_MAX / float(c.VIDEO_HEIGHT)
        autoZoom = min(widthRatio,heightRatio, 4) # magic, the four is max zoom
        c.SCALAR = float(autoZoom)
        self.zoomSlider.overwrite(autoZoom / 4) # lol magic
    
    def handle_video_buttons(self):
        if not c.isImage:
            self.handle_play_button()
            self.handle_video_left_arrow()
            self.handle_video_right_arrow_and_playback()

    """ video player handling functions"""
    def handle_play_button(self):
        b = self.buttons.get(ButtonIndices.PLAY)
        if b.clicked:
            b.isAlt = not b.isAlt
    
    def stop_playback(self):
        self.buttons.get(ButtonIndices.PLAY).isAlt = False
        
    def track_video(self, key):
        """called from event loop when they press one of the valid keys in keyshift"""
        seekDistance = SCRUB_KEYSHIFT[key]
        frame = self.video_slider.move_active_frame(seekDistance) 
        if frame is not None:
            self.frame = frame
    
    def handle_video_right_arrow_and_playback(self):
        """ moves video forward if we are playing or if the user clicks the right arrow """
        b = self.buttons.get(ButtonIndices.PLAY)
        video_is_playing = b.isAlt
        if (video_is_playing or self.get_button_clicked(ButtonIndices.RIGHT)):
            seekDistance = 2 if video_is_playing else 1
            frame = self.video_slider.move_active_frame(seekDistance)
            if frame is not None:
                self.frame = frame

    def handle_video_left_arrow(self):
        if self.get_button_clicked(ButtonIndices.LEFT):
            self.stop_playback()
            frame = self.video_slider.move_active_frame(-1)
            if frame is not None:
                self.frame = frame

    def handle_calibrate_buttons(self):
        self.handle_auto_calibrate_button()
        self.handle_calibrate_field_button()
        self.handle_calibrate_next_button()

    def handle_auto_calibrate_button(self):
        if not self.get_button_clicked(ButtonIndices.AUTOCALIBRATE):
            return
        
        self.ai_error = None
        boards = autofindfield.get_board(self.frame)
        self.bounds = None
        self.nextBounds = None
        self.boundsManager = None

        if len(boards) == 0: #fail.
            self.ai_error = ErrorMessage("Couldn't find any Tetris boards")
        else:
            self.nextBounds = None
            self.bounds = None
            self.boundsManager = BoundsPicker(boards, c, self.handle_auto_board_selected, False)
            if len(boards) > 1:
                max_board = min(len(boards),BoundsPicker.MAX_KEYBOARD_INDEX-1)
                self.ai_error = ErrorMessage("Multiple boards detected; please click one "
                                             f"(or press key 1-{max_board})!", BRIGHT_GREEN)
            
        
    def handle_auto_board_selected(self, board, suggested):
        """
        Called when the board_picker finds a suitable bound
        """
        self.boundsManager = None
        self.bounds = Bounds(False, config=c)
        self.bounds.setRect(board)
        self.bounds.setSubRect(suggested.inner_box)
        self.bounds.set()
        self.ai_error = None

        pixels, preview_layout = autofindfield.get_next_box(self.frame, board, suggested)
        if pixels is not None:
            self.nextBounds = Bounds(True, config=c)
            self.nextBounds.setRect(pixels)
            self.nextBounds.setSubRect(preview_layout.inner_box)
            self.nextBounds.sub_rect_name = preview_layout.name

        else:
            self.ai_error = ErrorMessage("Couldn't find the Next box could not be found")
        
    def handle_calibrate_field_button(self):
        if not self.get_button_clicked(ButtonIndices.CALLIBRATE):
            return
        self.ai_error = None
        self.bounds = Bounds(False, config=c)
        if self.nextBounds is not None:
            self.nextBounds.set()
        self.boundsManager = None
    
    def handle_calibrate_next_button(self):
        if not self.get_button_clicked(ButtonIndices.NEXTBOX):
            return
        self.ai_error = None
        self.nextBounds = Bounds(True, config=c)
        if self.bounds is not None:
            self.bounds.set()
        self.boundsManager = None

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

    def handle_render_button(self, force=False): #force == enter key
        """
        Returns None (error), 
        [] for image, and 
        [list of data] for video
        """
        if not self.buttons.get(ButtonIndices.RENDER).clicked and not force:
            return

        c.startLevel = self.get_button_value(ButtonIndices.LEVEL)

        # If not callibrated, do not allow render
        if not self.bounds_valid():
            self.error = ErrorMessage("You must set bounds for the board and next box.")
            return
        
        if not c.isImage:
            frame, _ = c.goToFrame(self.vcap, self.video_slider.left_frame)
        else:
            frame = self.frame
                
        board = self.bounds.getMinos(frame)
        mask = extractCurrentPiece(board)
        currPiece = getPieceMaskType(mask)
        preview = self.nextBounds.getMinos(frame)
        if currPiece is None:
            self.error = ErrorMessage("The current piece must be near the top, fully visible.")
            return

        nextPiece = getNextBox(preview)
        if nextPiece is None:
            self.error = ErrorMessage("Four dots must be centered inside each mino for next box.")
            return
        
        print2d(board)
        print2d(preview)

                    
        if c.isImage: # We directly call analysis on the single frame

            print("Rendering...")

            board -= mask # remove current piece from board to get pure board state
            print2d(board)
            c.hzString = PieceMasks.timeline[self.hzNum][c.gamemode]
            pos = Position(board, currPiece, nextPiece,
                            placement = None, # we don't know the placement
                            level = self.get_button_value(ButtonIndices.LEVEL),
                            lines = self.get_button_value(ButtonIndices.LINES), 
                            score = self.get_button_value(ButtonIndices.SCORE))
            Analysis.analyze([pos], PieceMasks.timelineNum[c.gamemode][self.hzNum])

            return []

                        
        else:
            # When everything done, release the capture
            #self.vcap.release()

            # Exit callibration, initiate rendering with returned
            # parameters
            print("Hz num: ", PieceMasks.timelineNum[c.gamemode][self.hzNum])
            c.hzString = PieceMasks.timeline[self.hzNum][c.gamemode]
            return [self.video_slider.left_frame, self.video_slider.right_frame, 
                    self.bounds, self.nextBounds, 
                    self.get_button_value(ButtonIndices.LEVEL),
                    self.get_button_value(ButtonIndices.LINES),
                    self.get_button_value(ButtonIndices.SCORE), 
                    PieceMasks.timelineNum[c.gamemode][self.hzNum]]
    
    
    def get_button_value(self, index):
        return self.buttons.get(index).value()

    def get_button_clicked(self, index):
        return self.buttons.get(index).clicked

    def clear_bounds(self):
        self.bounds = None
    def clear_nextBounds(self):
        self.nextBounds = None
    def clear_boundsManager(self):
        self.boundsManager = None

    def handle_bounds(self):
        for bound, deassign in [(self.bounds, self.clear_bounds),
                                (self.nextBounds, self.clear_nextBounds),
                                (self.boundsManager, self.clear_boundsManager)]:
        
            if bound is not None:
                delete = bound.updateMouse(*self.mouse_status.bounds_handler())
                if delete:
                    deassign()

    
    def handle_bounds_click(self):
        for item in [self.boundsManager, self.bounds, self.nextBounds]:
            if item is not None:
                item.click(self.mouse_status.x,self.mouse_status.y)
        
    def update_video_drag(self):
        self.video_dragger.update(self.mouse_status, c)
        
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
        if self.get_button_clicked(ButtonIndices.SAVE):

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

            data = [self.hzNum, bData, nData, c.COLOR_CALLIBRATION, c.SCALAR]
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

        self.colorSlider.overwrite(c.COLOR_CALLIBRATION / COLOR_CALIB_CONST)
        self.zoomSlider.overwrite(c.SCALAR / 4)
        self.hzSlider.overwrite(self.hzNum)

            
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

    def render_bounds(self):
        """
        renders the bounds
        Technically order matters, however boundsManager and bounds 
        should never both be non-null
        """
        surface = c.get_video_render_surface(transparent=True)
        for bound in (self.bounds, self.nextBounds, self.boundsManager):
            if bound is not None:
                bound.displayBounds(surface, nparray=self.frame)
                
        c.screen.blit(surface,[0,0])

    def render_sliders(self):
        slider_args = self.mouse_status.slider_handler()
        # Draw sliders
        c.COLOR_CALLIBRATION = COLOR_CALIB_CONST * self.colorSlider.tick(c.screen, c.COLOR_CALLIBRATION / COLOR_CALIB_CONST, *slider_args)
        c.SCALAR = max(0.1,4 * self.zoomSlider.tick(c.screen, c.SCALAR / 4, *slider_args))
        self.hzNum = self.hzSlider.tick(c.screen, self.hzNum, *slider_args)
        c.screen.blit(c.font.render(str(int(c.COLOR_CALLIBRATION)), True, WHITE), [1650, 900])
        

    def update_video_sliders(self):
        """ Updates the [ | ] video sliders. If they are dragged,
            we need to update the current frame."""
        if c.isImage:
            return
        frame = self.video_slider.update(self.mouse_status)
        if frame is not None:
            self.frame = frame

    def handle_space_release(self):
        """swaps the active videoSlider subcomponent"""
        if c.isImage:
            return
        frame = self.video_slider.toggle_active_frame()
        if frame is not None:
            self.frame = frame


    def render_error(self):
        # Draw error message
        if self.error is not None:
            if self.error.expired():
                self.error = None
            else:
                text = c.font2.render(self.error.text, True, self.error.color)
                c.screen.blit(text, [1670,1380])
        
        # this one doesnt expire; they have to click button to proceed
        if self.ai_error is not None:
            text = c.font2.render(self.ai_error.text, True, self.ai_error.color)
            c.screen.blit(text, [1720, 560])
            
    def render_text(self):
        # Draw timestamp
        if c.isImage:
            text = c.font.render("[No video controls]", True, WHITE)
            c.screen.blit(text, [80, 1373])
        else:
            timestamp_text = c.timestamp(self.video_slider.get_active_frame_number())
            text = c.font.render(timestamp_text, True, WHITE)
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

                c.resizeScreen(pygame, event)

        elif event.type == pygame.DROPFILE and event.file is not None:
            
            return str(event.file)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_status.start_press = True
            self.handle_left_click_event()
        elif event.type == pygame.MOUSEBUTTONUP:
            self.mouse_status.end_press = True
            self.handle_left_release_event()
        elif event.type == pygame.KEYDOWN:
            isTextBoxScroll, isKeyUsedForTextbox = self.buttons.updateTextboxes(event.key)
            if isTextBoxScroll:
                return
            if event.key in list(SCRUB_KEYSHIFT.keys()):
                self.track_video(event.key)
            elif event.key == pygame.K_RETURN:
                self.enterPressed = True
            elif event.key == pygame.K_t:
                # toggle next box subrectangle between
                # maxoutclub/regular/precise
                if self.nextBounds is not None:
                    self.nextBounds.cycle_sub_rect()
                    print ("Toggled preview bounds to:", self.nextBounds.sub_rect_name)
            elif event.key == pygame.K_b:
                # toggle board subrectangle between 
                # maxoutclub / regular
                if self.bounds is not None:
                    self.bounds.cycle_sub_rect()
                    print ("Toggled board bounds to:", self.bounds.sub_rect_name)
            elif event.key in BoundsPicker.KEYBOARD_KEYS and not isKeyUsedForTextbox:
                # numbers 1-9 for board selection
                if self.boundsManager is not None:
                    self.boundsManager.handle_keyboard_input(event.key)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                self.handle_space_release()

    def handle_pygame_events(self):        
        self.mouse_status.pre_update_event_loop()
        self.enterPressed = False
        for event in pygame.event.get():
            result = self.handle_pygame_event(event)
            if type(result) == str:
                return result
