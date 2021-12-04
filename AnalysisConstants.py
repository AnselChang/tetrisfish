from colors import WHITE, DARK_GREY
NONE = 0

INVALID = 1
BEST = 2
EXCELLENT = 3
MEDIOCRE = 4
RAPID = 5
INACCURACY = 6
MISTAKE = 7
BLUNDER = 8

MINOR_MISSED = 9
MAJOR_MISSED = 10

feedback = [BLUNDER, MISTAKE, INACCURACY, MEDIOCRE, EXCELLENT, BEST]
adjustment = [NONE, MINOR_MISSED, MAJOR_MISSED]


C_RAPID= [117,251,253]
C_BEST = [3, 160, 98] # dark green
C_MIST = [238,194,92] # orange
C_BLUN = [187,65,57] # red
C_EXCE = [159,230,91] # mid green
C_INAC = [255, 255, 0] # yellow
C_MEDI = [167*0.8, 227*0.8, 201*0.8]

feedbackColors = {RAPID: C_RAPID, BEST : C_BEST, EXCELLENT : C_EXCE, INACCURACY : C_INAC,
                  MISTAKE : C_MIST, BLUNDER : C_BLUN, NONE : WHITE, MAJOR_MISSED : C_BLUN,
                  MINOR_MISSED : C_INAC, INVALID : DARK_GREY, INVALID : WHITE, MEDIOCRE : C_MEDI}
feedbackString = {MEDIOCRE : "Mediocre", RAPID : "Rather Rapid", BEST : "Best Move", EXCELLENT : "Excellent Move", NONE : "Decent Move",
                  INACCURACY : "Inaccuracy", MISTAKE : "Mistake", BLUNDER : "Blunder", INVALID : "Unable to process"}

adjustmentString = {INVALID : "Invalid", MAJOR_MISSED : "Major Missed Adjust.", MINOR_MISSED : "Minor Missed Adjust.", NONE : ""}
