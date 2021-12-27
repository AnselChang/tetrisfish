"""
Class that keeps track of mouse coordinates for dragging video
"""
class VideoDragger:
    def __init__(self):
        self.active = False
        self.dragX = 0
        self.dragY = 0
        self.startX = 0
        self.startY = 0
         
    def start(self, mx, my, startX, startY):
        self.active = True
        self.dragX = mx
        self.dragY = my
        self.startX = startX
        self.startY = startY

    def update(self, mouse_status, config):
        if not mouse_status.left_pressed:
            return
        if mouse_status.out_of_bounds():
            return
        if not self.active:
            return
        config.VIDEO_X = self.mouse_status.x - self.dragX + self.startX
        config.VIDEO_Y = self.mouse_status.y - self.dragY + self.startY
    
    def stop(self):
        self.active = False