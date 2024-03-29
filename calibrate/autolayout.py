﻿"""
Helper classes for autocalibration
"""
import cv2  # Not actually necessary if you just want to create an image.
import numpy as np
from colors import COLOR_CYCLE

class AbstractLayout:
    def __init__(self, name, inner_box):
        self.name = name
        self.inner_box = inner_box

    def recalc_sub_rect(self, new_sub_rect):
        """Given a new subrect in nes_pixels, calculates inner_box"""
        print (new_sub_rect, self.nes_px_size)
        result = (new_sub_rect.left / float(self.nes_px_size[0]),
                  new_sub_rect.top / float(self.nes_px_size[1]),
                  new_sub_rect.right / float(self.nes_px_size[0]),
                  new_sub_rect.bottom / float(self.nes_px_size[1]))
        self.inner_box = result

    @property
    def inner_box_size(self):
        return [self.inner_box[2] - self.inner_box[0],
                self.inner_box[3] - self.inner_box[1]]

#layout for board
class Layout(AbstractLayout):
    def __init__(self, name, fillpoint, preview, inner_box=None):
        super().__init__(name, inner_box)
        self.name = name
        self.fillpoint = fillpoint # fill point in relative screen coords (x,y)
        self.preview = preview # preview type
    
    def clone(self):
        return Layout(self.name,self.fillpoint,self.preview,self.inner_box)

#layout for preview
class PreviewLayout(AbstractLayout):
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
    def fillpoint(self):
        # return inner box top left corner
        x = self.nes_px_size[0] * self.inner_box[0]
        y = self.nes_px_size[1] * self.inner_box[1]
        return (x,y)
        
    @property
    def inner_box_nespx(self):
        left = self.nes_px_size[0] * self.inner_box[0]
        top = self.nes_px_size[1] * self.inner_box[1]
        right = self.nes_px_size[0] * self.inner_box[2]
        bot = self.nes_px_size[1] * self.inner_box[3]
        return (left,top,right,bot)
    
    @property
    def should_suboptimize(self):
        """
        we should only do template matching if we have heaps of 
        black space around. Otherwise we will fail horrendously
        """
        if self.preview_type == self.HARDCODE:
            return False
        perc = self.inner_box_size[0] * self.inner_box_size[1]
        return perc < 0.9

    @property
    def inner_box_corners_nespx(self):
        box = self.inner_box_nespx
        return [(box[0],box[1]), #tl
                (box[0],box[3]), #bl
                (box[2],box[1]), #tr
                (box[2],box[3])] #br
        
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
                               self.preview_type,
                               self.preview_size)


#A bug/quirk; the key and name must match 1:1 for preview layouts
PREVIEW_LAYOUTS = { # stencil, stock capture etc.
                    "STANDARD": PreviewLayout("STANDARD", (96,56),(32,41), (0.04,0.41,0.96,0.78), PreviewLayout.STANDARD, 1.0),
                    # ctwc 2p                    
                    "MOC": PreviewLayout("MOC", (5.4*8,-3.1*8), (37,19), (0.08,0.16,0.90,0.89),PreviewLayout.TIGHT, 1.0),
                    # ctwc 4p
                    "MOC4pLeft": PreviewLayout("MOC4pLeft", (-5*8,4.5*8), (34,18), (0.05,0.07,0.97,0.95), PreviewLayout.TIGHT, 1.0),
                    "MOC4pRight": PreviewLayout("MOC4pRight", (10.8*8,4.5*8), (34,18), (0.05,0.07,0.97,0.95),PreviewLayout.TIGHT, 1.0),
                    # "CTM": #2p
                    # "CTM": #4p
                  }

FIELD_INNER_BOX = { 
                    "Standard": (0.01,0.0,0.99,0.993), #4 nespix black bottom
                    "MOC": (0.0,0.0,1.0,1.0) #fills entire area pretty much.
                  }
                    
                    
LAYOUTS = {"STANDARD": Layout("Standard", (0.5,0.5), 
                              PREVIEW_LAYOUTS["STANDARD"], FIELD_INNER_BOX["Standard"]),
           "RIGHT_SIDE": Layout("Standard", (0.75,0.5), 
                              PREVIEW_LAYOUTS["STANDARD"], FIELD_INNER_BOX["Standard"]),
           "STENCIL": Layout("Stencil™", (0.3,0.5), 
                              PREVIEW_LAYOUTS["STANDARD"], FIELD_INNER_BOX["Standard"]),
           "MOC_LEFT_2p": Layout("MaxoutClub", (0.422,0.302), 
                              PREVIEW_LAYOUTS["MOC"], FIELD_INNER_BOX["MOC"]), #ctwc 2p
           "MOC_RIGHT_2p": Layout("MaxoutClub", (0.578,0.302), 
                              PREVIEW_LAYOUTS["MOC"], FIELD_INNER_BOX["MOC"]), #ctwc 2p
           "MOC_TOPLEFT": Layout("MaxoutClub", (0.444,0.204), 
                              PREVIEW_LAYOUTS["MOC4pLeft"], FIELD_INNER_BOX["MOC"]), #ctwc 4p
           "MOC_TOPRIGHT": Layout("MaxoutClub", (0.556,0.204), 
                              PREVIEW_LAYOUTS["MOC4pRight"], FIELD_INNER_BOX["MOC"]), #ctwc 4p
           "MOC_BOTLEFT": Layout("MaxoutClub", (0.444,0.669), 
                              PREVIEW_LAYOUTS["MOC4pLeft"],FIELD_INNER_BOX["MOC"]), #ctwc 4p
           "MOC_BOTRIGHT": Layout("MaxoutClub", (0.556,0.669), 
                              PREVIEW_LAYOUTS["MOC4pRight"],FIELD_INNER_BOX["MOC"]) #ctwc 4p
          }

def generate_generic_layouts():
    result = {}
    for x in [0.1,0.20,0.37,0.7,0.85]:
        for y in [0.3, 0.65]:
            layout = Layout("Generic", (x, y),
                            PREVIEW_LAYOUTS["MOC"], FIELD_INNER_BOX["MOC"])
            result[f"{x}, {y}"] = layout
    return result

GENERIC_LAYOUTS = generate_generic_layouts()

def color_layout(image, layout, color, layout_name, RES):
    color.reverse # rgb <-> bgr
    center = layout.fillpoint
    center = int(center[0] * RES[1]), int(center[1] * RES[0])
    image = cv2.circle(image, center, 10, color, -1)
    center = center[0] + 10, center[1] + 10
    image = cv2.putText(image, layout_name, center, cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, color, 1, cv2.LINE_AA)
    return image

def generate_documentation_fields():
    RES = [720, 1280]
    # make rgb image
    image = np.zeros(RES + [3], np.uint8)
    
    for name, layout in GENERIC_LAYOUTS.items():
        image = color_layout(image, layout, [64,64,64], name,  RES)

    for index, (name, layout) in enumerate(LAYOUTS.items()):
        color = COLOR_CYCLE[index % len(COLOR_CYCLE)]
        image = color_layout(image, layout, color, name, RES)

    #cv2.imshow("hi", image)
    #cv2.waitKey(0)
    cv2.imwrite("docs/board_calibration/field-circles.png", image)


def generate_documentation_previews():
    SCALE_MULT = 5
    RES = [220 * SCALE_MULT, 220 * SCALE_MULT]

    # make rgb image
    image = np.zeros(RES + [3], np.uint8)
    TL = [70 * SCALE_MULT, 40 * SCALE_MULT]
    BR = [TL[0] + 80 * SCALE_MULT, TL[1] + 160 * SCALE_MULT]
    cv2.rectangle(image, TL, BR, 
                 (0,255,0), -1)

    texts = []
    for layout in PREVIEW_LAYOUTS.values():
        offset = layout.nes_px_offset
        size = layout.nes_px_size
        tl = [TL[0] + offset[0]*SCALE_MULT, TL[1] + offset[1] * SCALE_MULT]
        br = [tl[0] + size[0] * SCALE_MULT, tl[1] + size[1] * SCALE_MULT]
        tl = [int(i) for i in tl]
        br = [int(i) for i in br]
        
        cv2.rectangle(image, tl, br, (0,0,255,128), -1)
        inner_rect = layout.inner_box_nespx
        tl2 = [tl[0] + inner_rect[0]*SCALE_MULT, tl[1] + inner_rect[1] * SCALE_MULT]
        br2 = [tl[0] + inner_rect[2]*SCALE_MULT, tl[1] + inner_rect[3] * SCALE_MULT]
        tl2 = [int(i) for i in tl2]
        br2 = [int(i) for i in br2]
        cv2.rectangle(image, tl2, br2, (255,0,0,128), -1)
        texts.append([image, layout.name, tl.copy()])
    
    for text in texts:
        cv2.putText(*text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)

    #cv2.imshow("hi", image)
    #cv2.waitKey(0)
    cv2.imwrite("docs/board_calibration/field-previews.png", image)

# run this with
# python -m calibrate.autolayout
if __name__ == "__main__":
    generate_documentation_fields()
    generate_documentation_previews()
