"""
Helper classes for autocalibration
"""
class Layout:
    def __init__(self, name, fillpoint, preview):
        self.name = name
        self.fillpoint = fillpoint # fill point in relative screen coords (x,y)
        self.preview = preview # preview type

class PreviewLayout:
    STANDARD=0 # NEXT text then preview
    PRECISE=1 # tightest bounding box possible
    NO_TEXT=2 # minos sames size as field; centred in a large box
    HARDCODE=3
    def __init__(self, name, nes_px_offset, nes_px_size, inner_box, preview_type):
        self.name = name
        self.nes_px_offset = nes_px_offset
        self.nes_px_size = nes_px_size
        self.inner_box = inner_box
        self.preview_type = preview_type
    
    @property
    def inner_box_size(self):
        return [self.inner_box[2] - self.inner_box[0],
                self.inner_box[3] - self.inner_box[1]]
    @property
    def fillpoint(self):
        """
        returns where to floodfill in nes_px units
        """        
        if self.preview_type == self.STANDARD:
            return 0.10 * self.nes_px_size[0], 0.27 * self.nes_px_size[1]
        else: #fill from top left of rect, offset by 2 nes pixels 
            return 2, 2
        
    def __str__(self):
        return (f"PreviewLayout: {self.preview_type}")
    
    def __eq__(self, other):
        if not isinstance(other, PreviewLayout):
            return False
        return (self.nes_px_offset == other.nes_px_offset and
               self.nes_px_size == other.nes_px_size and
               self.preview_type == other.preview_type)


PREVIEW_LAYOUTS = { "STANDARD": PreviewLayout("Standard", (96,56),(32,42), (0.04,0.41,0.96,0.75),PreviewLayout.STANDARD),
                    # 5.5 tiles right, 3 tiles up. 4.5 tiles wide, 2.4 tiles high
                    "MOC": PreviewLayout("MOC", (5.5*8,-3*8),(4.5*8,2.4*8),(0.11,0.16,0.87,0.89),PreviewLayout.NO_TEXT) }

LAYOUTS = {"STANDARD": Layout("Standard", (0.5,0.5), PREVIEW_LAYOUTS["STANDARD"]),
           "RIGHT_SIDE": Layout("Standard", (0.75,0.5), PREVIEW_LAYOUTS["STANDARD"]),
           "STENCIL": Layout("Stencil™", (0.3,0.5), PREVIEW_LAYOUTS["STANDARD"]),
           "MOC_LEFT": Layout("MaxoutClub", (0.422,0.302), PREVIEW_LAYOUTS["MOC"])
          }

class Rect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
    
    @property
    def width(self):
        return self.right - self.left
    
    @property
    def height(self):
        return self.bottom - self.top

    @property
    def area(self):
        return self.width * self.height

    def to_array(self):
        return (self.left, self.top, self.right, self.bottom)
    
    def __str__(self):
        return str(self.to_array())
   
    def __eq__(self, other):
        if isinstance(other, Rect):
            return (self.left == other.left and
                   self.top == other.top and
                   self.right == other.right and
                   self.bottom == other.bottom)
        return False

    def within(self, yx):
        """
        returns if rectangle is within an image with given y/x size.
        """
        return (0 <= self.left <= self.right <= yx[1] and 
                0 <= self.top <= self.bottom <= yx[0])
           
        