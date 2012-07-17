def setSessionWindowDimensions():
    session.windowWidth = int( request.vars.width )
    session.windowHeight = int( request.vars.height )

def setTextWidthMetric():
    session.textWidthMetric = float( request.vars.width ) * 1.25 if request.vars.width else 0

def setPageHeight():
    session.pageHeight = int( request.vars.pageHeight ) if request.vars.pageHeight else 0

def setScrollbarWidth():
    session.scrollbarWidth = int( request.vars.width ) if request.vars.width else 0
