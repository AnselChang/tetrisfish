from colors import WHITE
NONE = 0


INACCURACY = 1
MISTAKE = 2
EXCELLENT = 3
BEST = 4
BLUNDER = 5
RAPID = 6

MAJOR_MISSED = 7
MINOR_MISSED = 8


C_RAPID= [81,170,165]
C_BEST = [3, 160, 98] # dark green
C_MIST = [238,194,92] # orange
C_BLUN = [187,65,57] # red
C_EXCE = [159,187,91] # mid green
C_INAC = [255, 255, 0] # yellow

feedbackColors = {RAPID: C_RAPID, BEST : C_BEST, EXCELLENT : C_EXCE, INACCURACY : C_INAC,
                  MISTAKE : C_MIST, BLUNDER : C_BLUN, NONE : WHITE}
feedbackString = {RAPID : "Rather Rapid", BEST : "Best Move", EXCELLENT : "Excellent Move", NONE : "Decent Move",
                  INACCURACY : "Inaccuracy", MISTAKE : "Mistake", BLUNDER : "Blunder"}

adjustmentString = {MAJOR_MISSED : "Major Missed Adjustment", MINOR_MISSED : "Minor Missed Adjustment", NONE : ""}
