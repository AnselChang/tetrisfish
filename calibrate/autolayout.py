"""
Helper classes for autocalibration
"""
class Layout:
    def __init__(self, name, fillpoint, preview):
        self.name = name
        self.fillpoint = fillpoint # fill point in relative screen coords (x,y)
        self.preview = preview # preview type

class PreviewLayout:    
    TIGHT=1
    STANDARD=2 # flood fill the box, then choose subset based on nes_px_size    
    HARDCODE=3 # don't expand, just hardcode it.
    
    def __init__(self, name, nes_px_offset, nes_px_size, inner_box, preview_type, preview_size):
        self.name = name
        self.nes_px_offset = nes_px_offset #e.g. (90, 90)
        self.nes_px_size = nes_px_size #e.g (42, 32)
        self.inner_box = inner_box # e.g. (0.1, 0.1, 0.9, 0.9)
        self.preview_type = preview_type
        self.preview_size = preview_size #e.g. 1.0

    @property
    def inner_box_size(self):
        return [self.inner_box[2] - self.inner_box[0],
                self.inner_box[3] - self.inner_box[1]]
    
    @property
    def fillpoint(self):
        # return inner box top left corner + 2 nes pixels
        x = self.nes_px_size[0] * self.inner_box[0] + 2
        y = self.nes_px_size[1] * self.inner_box[1] + 2
        return (x,y)
        
    @property
    def inner_box_nespx(self):
        left = self.nes_px_size[0] * self.inner_box[0]
        top = self.nes_px_size[1] * self.inner_box[1]
        right = self.nes_px_size[0] * self.inner_box[2]
        bot = self.nes_px_size[1] * self.inner_box[3]
        return (left,top,right,bot)
        
    def __str__(self):
        return (f"PreviewLayout: {self.nes_px_offset}, {self.preview_type}")
    
    def __eq__(self, other):
        if not isinstance(other, PreviewLayout):
            return False
        return (self.nes_px_offset == other.nes_px_offset and
               self.preview_type == other.preview_type and
               self.nes_px_size == other.nes_px_size and
               self.inner_box == other.inner_box)

    def clone(self):
        return PreviewLayout(self.name,
                               self.nes_px_offset,
                               self.nes_px_size,
                               self.inner_box,
                               self.preview_type)


#A bug/quirk; the key and name must match 1:1 for preview layouts
PREVIEW_LAYOUTS = { # stencil, stock capture etc.
                    "STANDARD": PreviewLayout("STANDARD", (96,56),(32,42), (0.04,0.41,0.96,0.75), PreviewLayout.STANDARD, 1.0),
                    # ctwc 2p                    
                    "MOC": PreviewLayout("MOC", (5.4*8,-3.1*8), (37,19), (0.08,0.16,0.90,0.89),PreviewLayout.TIGHT, 1.0),
                    # ctwc 4p
                    "MOC4pLeft": PreviewLayout("MOC4pLeft", (-5*8,4.5*8), (34,18), (0.05,0.07,0.97,0.95), PreviewLayout.TIGHT, 1.0),
                    "MOC4pRight": PreviewLayout("MOC4pRight", (10.8*8,4.5*8), (34,18), (0.05,0.07,0.97,0.95),PreviewLayout.TIGHT, 1.0),
                    # "CTM": #2p
                    # "CTM": #4p
                  }


LAYOUTS = {"STANDARD": Layout("Standard", (0.5,0.5), PREVIEW_LAYOUTS["STANDARD"]),
           "RIGHT_SIDE": Layout("Standard", (0.75,0.5), PREVIEW_LAYOUTS["STANDARD"]),
           "STENCIL": Layout("Stencil™", (0.3,0.5), PREVIEW_LAYOUTS["STANDARD"]),
           "MOC_LEFT": Layout("MaxoutClub", (0.422,0.302), PREVIEW_LAYOUTS["MOC"]), #ctwc 2p
           "MOC_RIGHT": Layout("MaxoutClub", (0.578,0.302), PREVIEW_LAYOUTS["MOC"]), #ctwc 2p
           "MOC_TOPLEFT": Layout("MaxoutClub", (0.444,0.204), PREVIEW_LAYOUTS["MOC4pLeft"]), #ctwc 4p
           "MOC_TOPRIGHT": Layout("MaxoutClub", (0.556,0.204), PREVIEW_LAYOUTS["MOC4pRight"]), #ctwc 4p
           "MOC_BOTLEFT": Layout("MaxoutClub", (0.444,0.669), PREVIEW_LAYOUTS["MOC4pLeft"]), #ctwc 4p
           "MOC_BOTRIGHT": Layout("MaxoutClub", (0.556,0.669), PREVIEW_LAYOUTS["MOC4pRight"]) #ctwc 4p
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
    
    def contains(self, xy):
        return (self.left <= xy[0] <= self.right and 
               self.top <= xy[1] <= self.bottom)

    def within(self, yx):
        """
        returns if rectangle is within an image with given y/x size.
        """
        return (0 <= self.left <= self.right <= yx[1] and 
                0 <= self.top <= self.bottom <= yx[0])
           
        