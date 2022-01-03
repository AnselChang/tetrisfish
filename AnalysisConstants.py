from colors import WHITE, DARK_GREY, MID_GREY
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

feedback = [BLUNDER, MISTAKE, INACCURACY, MEDIOCRE, EXCELLENT, BEST, RAPID]
adjustment = [NONE, MINOR_MISSED, MAJOR_MISSED]


C_RAPID= [117,251,253]
C_BEST = [3, 160, 98] # dark green
C_MIST = [230,125,56] # orange
C_BLUN = [187,65,57] # red
C_EXCE = [159,230,91] # mid green
C_INAC = [255, 255, 0] # yellow
C_MEDI = [167*0.8, 227*0.8, 201*0.8]


# From a score of 0-100, return a color
def scoreToColor(score, isKs):

    if score == -1:
        return WHITE
    
    if isKs:
        if score > 100:
            return C_RAPID
        elif score >= 80:
            return C_BEST
        elif score >= 65:
            return C_EXCE
        elif score >= 50:
            return C_MEDI
        elif score >= 35:
            return C_INAC
        elif score >= 20:
            return C_MIST
        else:
            return C_BLUN

        
    if score > 100:
        return C_RAPID
    elif score >= 93:
        return C_BEST
    elif score >= 90:
        return C_EXCE
    elif score >= 87:
        return C_MEDI
    elif score >= 84:
        return C_INAC
    elif score >= 81:
        return C_MIST
    else:
        return C_BLUN

INVALID_COLOR = MID_GREY


feedbackColors = {RAPID: C_RAPID, BEST : C_BEST, EXCELLENT : C_EXCE, INACCURACY : C_INAC,
                  MISTAKE : C_MIST, BLUNDER : C_BLUN, NONE : WHITE, MAJOR_MISSED : C_BLUN,
                  MINOR_MISSED : C_INAC, INVALID : INVALID_COLOR, MEDIOCRE : C_MEDI}
feedbackString = {MEDIOCRE : "Mediocre", RAPID : "Rather Rapid", BEST : "Best Move", EXCELLENT : "Excellent",
                  INACCURACY : "Inaccuracy", MISTAKE : "Mistake", BLUNDER : "Blunder", INVALID : "ERROR"}

adjustmentString = {INVALID : "Invalid", MAJOR_MISSED : "Major Missed Adj.", MINOR_MISSED : "Minor Missed Adj.", NONE : ""}
