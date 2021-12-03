from colors import WHITE, DARK_GREY
NONE = 0

INVALID = 1
INACCURACY = 2
MISTAKE = 3
EXCELLENT = 4
MINOR_MISSED = 5
BEST = 6
BLUNDER = 7
RAPID = 8
MAJOR_MISSED = 9


C_RAPID= [117,251,253]
C_BEST = [3, 160, 98] # dark green
C_MIST = [238,194,92] # orange
C_BLUN = [187,65,57] # red
C_EXCE = [159,187,91] # mid green
C_INAC = [255, 255, 0] # yellow

feedbackColors = {RAPID: C_RAPID, BEST : C_BEST, EXCELLENT : C_EXCE, INACCURACY : C_INAC,
                  MISTAKE : C_MIST, BLUNDER : C_BLUN, NONE : WHITE, MAJOR_MISSED : C_BLUN,
                  MINOR_MISSED : C_INAC, INVALID : DARK_GREY, INVALID : WHITE}
feedbackString = {RAPID : "Rather Rapid", BEST : "Best Move", EXCELLENT : "Excellent Move", NONE : "Decent Move",
                  INACCURACY : "Inaccuracy", MISTAKE : "Mistake", BLUNDER : "Blunder", INVALID : "Unable to process"}

adjustmentString = {INVALID : "Invalid", MAJOR_MISSED : "Major Missed Adjust.", MINOR_MISSED : "Minor Missed Adjust.", NONE : ""}
