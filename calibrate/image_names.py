C_NTSC = "ntsc"
C_PAL = "pal"
C_ABOARD = "autocaliboard"
C_ABOARD2 = "autocaliboard2"
C_BOARD = "calliboard"
C_BOARD2 = "calliboard2"
C_NEXT = "nextbox"
C_NEXT2 = "nextbox2"
C_PLAY = "play"
C_PLAY2 = "play2"
C_PAUSE = "pause"
C_PAUSE2 = "pause2"
C_PREVF = "prevframe"
C_PREVF2 = "prevframe2"
C_NEXTF = "nextframe"
C_NEXTF2 = "nextframe2"
C_RENDER = "render"
C_RENDER2 = "render2"
C_SLIDER = "slider"
C_SLIDER2 = "slider2"
C_SLIDERF = "sliderflipped"
C_SLIDER2F = "slider2flipped"

C_LVIDEO = "leftvideo"
C_LVIDEO2 = "leftvideo2"
C_RVIDEO = "rightvideo"
C_RVIDEO2 = "rightvideo2"
C_LVIDEORED = "leftvideored"
C_LVIDEORED2 = "leftvideored2"
C_RVIDEORED = "rightvideored"
C_RVIDEORED2 = "rightvideored2"
C_SEGMENT = "segment"
C_SEGMENTGREY = "segmentgrey"

C_SAVE = "upload"
C_LOAD = "download"

C_CHECKMARK = "checkmark"
C_CHECKMARK2 = "checkmark2"

CALLIBRATION_IMAGES = [C_NTSC, C_PAL, C_BOARD, C_BOARD2, C_NEXT, C_NEXT2, C_PLAY, C_PLAY2, C_PAUSE, C_PAUSE2, C_SEGMENT, C_SEGMENTGREY, C_ABOARD, C_ABOARD2]
CALLIBRATION_IMAGES.extend( [C_PREVF, C_PREVF2, C_NEXTF, C_NEXTF2, C_RENDER, C_RENDER2, C_SLIDER, C_SLIDER2, C_SLIDERF, C_SLIDER2F] )
CALLIBRATION_IMAGES.extend([ C_LVIDEO, C_LVIDEO2, C_RVIDEO, C_RVIDEO2, C_SAVE, C_LOAD ])
CALLIBRATION_IMAGES.extend([ C_LVIDEORED, C_LVIDEORED2, C_RVIDEORED, C_RVIDEORED2, C_CHECKMARK, C_CHECKMARK2 ])