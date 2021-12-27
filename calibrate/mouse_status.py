"""
Simple data structure that holds current mouse status
"""
import pygame
import config as c #todo: remove this dependency

class MouseStatus:
    def __init__(self):
        self.x = x
        self.y = y
        self.left_pressed = False
        self.left_release = False
        self.start_press = False #whether we just mouse-downed 
        self.end_press = False #whether we just mouse-up'ed

    def slider_handler(self):
        return (self.start_press, self.left_pressed, self.x, self.y)

    def bounds_handler(self):
        return (self.x, self.y, self.start_press, self.end_press)

    def pygame_button_handler(self):
        return (self.x, self.y, self.end_press)
    
    def start_frame_update(self):
        self.x, self.y = c.getScaledPos(*pygame.mouse.get_pos())
        self.left_pressed =  pygame.mouse.get_pressed()[0]
        
    def pre_update_event_loop(self):
        """        
        1) update all widgets
        2) pre update 
        3) event loop (which will update startpress)
        """
        self.end_press = False
        self.start_press = False

    def mouseOutOfBounds(self):
        return not (0 <= self.x <= c.X_MAX and
                    0 <= self.y <= c.Y_MAX)
