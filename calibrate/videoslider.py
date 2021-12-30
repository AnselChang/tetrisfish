"""
Class that manages mouse and keyboard input for the slider,
as well as rendering the three slider components
"""

#todo: remove reliance on vcap :(
from enum import Enum
from TetrisUtility import clamp
import pygame

class ActiveSubSlider:
    LEFT = 0
    RIGHT = 1
    SEGMENT = 2

class VideoSlider:
    
    DEFAULT_X = 497
    DEFAULT_WIDTH = 922
    DEFAULT_Y = 1377
    DEFAULT_SHAPE = (DEFAULT_X, DEFAULT_Y, DEFAULT_WIDTH)
    def __init__(self, c, sliderComponents, shape, vcap):
        
        # addresses a particular frame number
        self.left_frame = 0
        self.right_frame = c.totalFrames - 100
        self.segment_frame = 0
        
        # which slider (left, right, segment) we are editing
        self.active_frame = ActiveSubSlider.LEFT
        
        self.leftSlider, self.rightSlider, self.segmentred, self.segmentgrey = sliderComponents

        self.set_slider_alts()


        self.X,self.Y,self.WIDTH = shape
        self.vcap = vcap
        self.c = c

    def get_active_frame_number(self):
        if self.active_frame == ActiveSubSlider.LEFT:
            return self.left_frame
        if self.active_frame == ActiveSubSlider.RIGHT:
            return self.right_frame
        if self.active_frame == ActiveSubSlider.SEGMENT:
            return self.segment_frame
    
    def set_active_frame_number(self, new_value):
        if self.active_frame == ActiveSubSlider.LEFT:
            self.left_frame = new_value
        if self.active_frame == ActiveSubSlider.RIGHT:
            self.right_frame = new_value
        if self.active_frame == ActiveSubSlider.SEGMENT:
            self.segment_frame = new_value

    def set_slider_alts(self):
        self.rightSlider.setAlt(self.active_frame == ActiveSubSlider.RIGHT)
        self.leftSlider.setAlt(self.active_frame == ActiveSubSlider.LEFT)

    def update_segment(self, mouse_status):
        """
        Moves the segment frame if the mouse is down.
        Then renders it (gray, invis or red) based on current status.
        """
        mx , my = mouse_status.pos
        c = self.c
        inVideoSlider = (self.X - 20 <= mx <= self.X + self.WIDTH + 20 and self.Y - 30 <= my <= self.Y + 60)
        # calculate whether we are active.        
        frame = None
        if not self.leftSlider.active and not self.rightSlider.active and inVideoSlider:
            if mouse_status.left_pressed:
                self.active_frame = ActiveSubSlider.SEGMENT
                self.set_slider_alts()
                self.segment_frame = clamp((c.totalFrames) * (mx - self.X) / self.WIDTH, 0, c.totalFrames - 100)
                frame, self.segment_frame = c.goToFrame(self.vcap, self.segment_frame)
            elif not self.leftSlider.isHovering(mx,my) and not self.rightSlider.isHovering(mx,my):
                self.c.screen.blit(self.segmentgrey, [mx - 10, self.Y]) #draw

        if self.active_frame == ActiveSubSlider.SEGMENT: #draw red
            self.c.screen.blit(self.segmentred, [self.X - 5 + self.WIDTH * self.segment_frame / (c.totalFrames - 1) , self.Y])

        return frame

    def update_sides(self, mouse_status):
        """
            Updates the active slider (left or right).
            If either of them are active, returns the current frame
            If neither of them are active, returns None.
        """
        slider_args = mouse_status.slider_handler()
        c = self.c
        # Draw video bounds sliders
        slider_args = slider_args + [True]
        self.right_frame = self.rightSlider.tick(c.screen, self.right_frame / (c.totalFrames - 1), *slider_args)
        self.right_frame = clamp(int(self.right_frame * c.totalFrames), 0, c.totalFrames - 100)
        slider_args = [slider_args[0] and not self.rightSlider.active] + slider_args[1:]
        self.left_frame = self.leftSlider.tick(c.screen, self.left_frame / (c.totalFrames - 1), *slider_args)
        self.left_frame = clamp(int(self.left_frame * c.totalFrames),0,c.totalFrames - 100)

        # Update frame from video sliders
        if self.rightSlider.active:            
            self.active_frame = ActiveSubSlider.RIGHT
            self.set_slider_alts()
            return self.update_active_frame(self.get_active_frame_number())
        elif self.leftSlider.active:            
            self.active_frame = ActiveSubSlider.LEFT
            self.set_slider_alts()
            return self.update_active_frame(self.get_active_frame_number())
        return None

    def update(self, mouse_status):
        """Updates the sliders and returns a new video frame if anything was scrubbed"""
        frame = self.update_sides(mouse_status)
        frame2 = self.update_segment(mouse_status)
        if frame is not None:
            return frame
        return frame2

    def move_active_frame(self, count):
        # move the active slider by [count] frames
        # returns the new frame from the video capture device.
        # Will return None if we are trying to move the slider to an illegal
        # position
        
        new_frame = self.get_active_frame_number() + count
        if new_frame < 0 or new_frame > self.c.totalFrames - 100:
            return None
        
        return self.update_active_frame(new_frame)        

    def toggle_active_frame(self):
        """
           Swaps the active frame from Left/Right. 
           If its the | segment, transfers it to left
        """
        
        if self.active_frame == ActiveSubSlider.LEFT:
            self.active_frame = ActiveSubSlider.RIGHT
        else:
            self.active_frame = ActiveSubSlider.LEFT
        self.rightSlider.setAlt(self.active_frame == ActiveSubSlider.RIGHT)
        self.leftSlider.setAlt(self.active_frame == ActiveSubSlider.LEFT)
        

        return self.update_active_frame(self.get_active_frame_number())
        

    def update_active_frame(self, target):
        """ 
            Seek to target frame on the active frame pointer 
            Then set current frame counter to that value
            returns the new frame
        """
        
        frame, new_value = self.c.goToFrame(self.vcap, target)
        self.set_active_frame_number(new_value)
        return frame

    def go_to_active_frame(self):
        self.update_active_frame(self.get_active_frame_number())
