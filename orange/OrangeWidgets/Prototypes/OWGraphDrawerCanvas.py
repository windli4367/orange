CIRCLE=0
SQUARE=1
ROUND_RECT=2

NOTHING = 0
ZOOMING = 1
SELECT_RECTANGLE = 2
SELECT_POLYGON = 3
MOVE_SELECTION = 4

import copy

from OWGraph import *
from Numeric import *
from orngScaleScatterPlotData import *
from OWGraphTools import UnconnectedLinesCurve

class OWGraphDrawerCanvas(OWGraph):
    def __init__(self, graphDrawWidget, parent = None, name = "None"):
        OWGraph.__init__(self, parent, name)
        self.parent = parent
        self.labelText = []
        self.tooltipText = []
        self.vertices = {}         # slovar vozlisc oblike  orngIndex: vertex_objekt
        self.edges = {}            # slovar povezav oblike  curveKey: edge_objekt
        self.indexPairs = {}       # slovar oblike CurveKey: orngIndex   (za vozlisca)
        self.selection = []        # seznam izbranih vozlisc (njihovih indeksov)
        self.selectionStyles = {}  # slovar stilov izbranih vozlisc
        self.colorIndex = -1
        self.visualizer = None
        self.selectedCurve = None
        self.selectedVertex = None
        self.vertexDegree = []     # seznam vozlisc oblike (vozlisce, stevilo povezav), sortiran po stevilu povezav
        self.edgesKey = -1
        self.vertexSize = 6
        self.nVertices = 0
        self.xData = []
        self.yData = []
        self.enableXaxis(0)
        self.enableYLaxis(0)
        self.state = NOTHING  #default je rocno premikanje
        
    def addSelection(self, ndx):
        #print("add selection")
        if not ndx in self.selection:
            self.selectionStyles[ndx] = self.curve(self.vertices[ndx]).symbol().brush().color().name()
            newSymbol = QwtSymbol(QwtSymbol.Ellipse, QBrush(Qt.green), QPen(Qt.green), QSize(6, 6))
            self.setCurveSymbol(self.vertices[ndx], newSymbol)
            self.selection.append(ndx);
            self.replot()
            return True
        
        return False

            
    def removeSelection(self):
        #print("remove selection")
        for v in self.selection:
            newSymbol = QwtSymbol(QwtSymbol.Ellipse, QBrush(QColor(self.selectionStyles[v])), QPen(QColor(self.selectionStyles[v])), QSize(6, 6))
            self.setCurveSymbol(self.vertices[v], newSymbol)
            
        self.selection = []
        self.selectionStyles = {}
        self.replot()
        
    def generateVertexPower(self):
        # init vertexPower
        for i in range(self.nVertices):
            self.vertexDegree.append((i,0))
            
        # calculate vertex power
        for e in range(self.nEdges):
            (key,i,j) = self.edges[e]
            (v_i,power_i) = self.vertexDegree[i]
            (v_j,power_j) = self.vertexDegree[j]
            
            self.vertexDegree[i] = (v_i, power_i + 1)
            self.vertexDegree[j] = (v_j, power_j + 1)
                    
        # sort ascending by power
        for i in range(self.nVertices - 1):
            for j in range(i, self.nVertices):
                (v_i,power_i) = self.vertexDegree[i]
                (v_j,power_j) = self.vertexDegree[j]
                
                if power_j > power_i:
                    self.vertexDegree[i] = (v_j,power_j)
                    self.vertexDegree[j] = (v_i,power_i)
        
    def selectHubs(self, no):
        if self.vertexDegree == []:
            self.generateVertexPower()
            
        count = 0
        old_power = -1
        next_power = -1     
        #print "no: " + str(no)
        while count < no or old_power == next_power:
            (v,old_power) = self.vertexDegree[count]
            
            next_power = -1
            if count < (len(self.vertexDegree) - 1):
                (next_v, next_power) = self.vertexDegree[count + 1]
                
            self.addSelection(v)
            #print "old_power: " + str(old_power) + " new_power: " + str(next_power)
            count += 1
            
    def selectConnectedNodes(self, distance):
        i = 0
        newSelections = -1
        while i < distance and newSelections <> 0:
            newSelections = 0
            selectedVertexes = []
        
            for v in self.selection:
                selectedVertexes.append(v)
            
            for v in selectedVertexes:
                for e in range(self.nEdges):
                    (key,i,j) = self.edges[e]
                    
                    if i == v:
                        if self.addSelection(j):
                            newSelections += 1
                    elif j == v:
                        if self.addSelection(i):
                            newSelections += 1
            
            i += 1
        
    def getSelectedExamples(self):
        if len(self.selection) == 0:
            return None
        
        indeces = self.visualizer.nVertices() * [0]
        
        for v in self.selection:
            indeces[v] = v + 1

        if self.visualizer.graph.items != None:
            return self.visualizer.graph.items.select(indeces)
        else:
            return None

    def getSelectedGraph(self):
        if len(self.selection) == 0:
            return None
        
        graph = orange.GraphAsList(len(self.selection), 0)
        
        for e in range(self.nEdges):
            (key,i,j) = self.edges[e]
            
            if (i in self.selection) and (j in self.selection):
                graph[self.selection.index(i), self.selection.index(j)] = 1
        
        indeces = self.visualizer.nVertices() * [0]
        
        for v in self.selection:
            indeces[v] = v + 1

        if self.visualizer.graph.items != None:
            graph.setattr("items", self.visualizer.graph.items.select(indeces))
            
        return graph

            
    def moveVertex(self, pos):
        # ce ni nic izbrano
        if self.selectedCurve == None:
            return
        #curve = self.curve(self.vertices[self.selectedVertex])  #self.selectedCurve je key
        #newX = self.invTransform(curve.xAxis(), pos.x())
        #newY = self.invTransform(curve.yAxis(), pos.y())

        newX = self.invTransform(2, pos.x())
        newY = self.invTransform(0, pos.y())


        self.visualizer.xCoors[self.selectedVertex] = newX
        self.visualizer.yCoors[self.selectedVertex] = newY
                
        self.setCurveData(self.vertices[self.selectedVertex], [newX], [newY])
        
        for e in range(self.nEdges):
            (key,i,j) = self.edges[e]

            if i == self.selectedVertex:
                self.xData[key*2] = newX
                self.yData[key*2] = newY
                #currEdgeObj = self.curve(key)
                #self.setCurveData(key, [newX, currEdgeObj.x(1)], [newY, currEdgeObj.y(1)])                    
            elif j == self.selectedVertex:
                self.xData[key*2 + 1] = newX
                self.yData[key*2 + 1] = newY
                #currEdgeObj = self.curve(key)
                #self.setCurveData(key, [currEdgeObj.x(0), newX], [currEdgeObj.y(0), newY])
      
        self.setCurveData(self.edgesKey, self.xData, self.yData)
    
    def onMouseMoved(self, event):
        if self.mouseCurrentlyPressed and self.state == MOVE_SELECTION:
            if len(self.selection) > 0:
                border=self.vertexSize/2
                maxx=max(take(self.visualizer.xCoors, self.selection))
                maxy=max(take(self.visualizer.yCoors, self.selection))
                minx=min(take(self.visualizer.xCoors, self.selection))
                miny=min(take(self.visualizer.yCoors, self.selection))
                #relativni premik v pikslih
                dx=event.pos().x() - self.GMmouseStartEvent.x()
                dy=event.pos().y() - self.GMmouseStartEvent.y()

                maxx=self.transform(self.xBottom, maxx) + border + dx
                maxy=self.transform(self.yLeft, maxy) + border + dy
                minx=self.transform(self.xBottom, minx) - border + dx
                miny=self.transform(self.yLeft, miny) - border + dy
                maxx=self.invTransform(self.xBottom, maxx)
                maxy=self.invTransform(self.yLeft, maxy)
                minx=self.invTransform(self.xBottom, minx)
                miny=self.invTransform(self.yLeft, miny)

                if maxx >= self.axisScale(self.xBottom).hBound():
                    return
                if minx <= self.axisScale(self.xBottom).lBound():
                    return
                if maxy >= self.axisScale(self.yLeft).hBound():
                    return
                if miny <=self.axisScale(self.yLeft).lBound():
                    return

                for ind in self.selection:
                    self.selectedVertex = ind
                    self.selectedCurve = self.vertices[ind]

                    vObj = self.curve(self.selectedCurve)
                    tx = self.transform(vObj.xAxis(), vObj.x(0)) + dx
                    ty = self.transform(vObj.yAxis(), vObj.y(0)) + dy
                    
                    tempPoint = QPoint(tx, ty)
                    self.moveVertex(tempPoint)

                self.GMmouseStartEvent.setX(event.pos().x())  #zacetni dogodek postane trenutni
                self.GMmouseStartEvent.setY(event.pos().y())
                self.replot()

        else:
            OWGraph.onMouseMoved(self, event)


    def onMousePressed(self, event):
        if self.state == MOVE_SELECTION:
            self.mouseCurrentlyPressed = 1
            if self.isPointSelected(self.invTransform(self.xBottom, event.pos().x()), self.invTransform(self.yLeft, event.pos().y())) and self.selection!=[]:
                self.GMmouseStartEvent = QPoint(event.pos().x(), event.pos().y())
                self.canvas().setMouseTracking(True)
            else:
                #pritisk na gumb izven izbranega podrocja ali pa ni izbranega podrocja
                self.selectVertex(event.pos())
                self.GMmouseStartEvent = QPoint(event.pos().x(), event.pos().y())
                self.canvas().setMouseTracking(True)

            #self.removeAllSelections()
        else:
            OWGraph.onMousePressed(self, event)


    def onMouseReleased(self, event):  
        if self.state == MOVE_SELECTION:
            self.mouseCurrentlyPressed = 0
            self.canvas().setMouseTracking(False)
            self.selectedCurve= None
            self.selectedVertex=None
            self.moveGroup=False
            #self.selectedVertices=[]
            self.GMmouseStartEvent=None
            
        elif self.state == SELECT_RECTANGLE:
            self.selectVertices()
            OWGraph.onMouseReleased(self, event)

        elif self.state == SELECT_POLYGON:
                OWGraph.onMouseReleased(self, event)
                if self.tempSelectionCurve == None:   #ce je OWVisGraph zakljucil poligon
                    self.selectVertices()
        else:
            OWGraph.onMouseReleased(self, event)
    
    def selectVertices(self):
        for vertexKey in self.indexPairs.keys():
            vObj = self.curve(vertexKey)
            
            if self.isPointSelected(vObj.x(0), vObj.y(0)):
                self.addSelection(self.indexPairs[vertexKey])
                
    def selectVertex(self, pos):
        #key, dist, xVal, yVal, index = self.closestCurve(pos.x(), pos.y())
        #curve = self.curve(key)
        min = 1000000
        ndx = -1
        #print "x: " + str(pos.x()) + " y: " + str(pos.y()) 
        #px = self.invTransform(curve.xAxis(), pos.x())
        #py = self.invTransform(curve.yAxis(), pos.y())   
        px = self.invTransform(2, pos.x())
        py = self.invTransform(0, pos.y())   
        #print "xAxis: " + str(curve.xAxis()) + " yAxis: " + str(curve.yAxis())
        #print "px: " + str(px) + " py: " + str(py)
        for v in range(self.nVertices):
            x1 = self.visualizer.xCoors[v]
            y1 = self.visualizer.yCoors[v]
            #print "x: " + str(x1) + " y: " + str(y1)
            dist = self.dist([px, py], [x1, y1])
            
            if dist < min:
                min = dist
                ndx = v
                
                if min < 10:
                    break
        
        if min < 10 and ndx != -1:
            self.addSelection(ndx)
        else:
            self.removeSelection()

#        key, dist, xVal, yVal, index = self.closestCurve(pos.x(), pos.y())
#
#        if key >= 0 and dist < 15:
#            if key in self.indexPairs.keys():   #to se zgodi samo, ce vozlisce ni povezano
#                self.addSelection(self.indexPairs[key])
#                return
#
#            curve = self.curve(key)  #to je povezava, ker so bile te z insertCurve() dodane prej,
#                                     #da se ne vidijo skozi vozlisca
#            
#            for e in range(self.nEdges):
#                (keyTmp,i,j) = self.edges[e]
#                if keyTmp == key:
#                    ndx1 = i
#                    ndx2 = j
#
#            vOb1 = self.curve(self.vertices[ndx1])
#            vOb2 = self.curve(self.vertices[ndx2])
#            
#            px = self.invTransform(curve.xAxis(), pos.x())
#            py = self.invTransform(curve.yAxis(), pos.y())
#
#            if self.dist([px, py], [vOb1.x(0), vOb1.y(0)]) <= self.dist([px, py], [vOb2.x(0), vOb2.y(0)]):
#                self.addSelection(ndx1)
#            else:
#                self.addSelection(ndx2)
#        else:
#            self.removeSelection()
            
    def dist(self, s1, s2):
        return math.sqrt((s1[0]-s2[0])**2 + (s1[1]-s2[1])**2)
    
    def updateData(self):
        self.removeDrawingCurves(removeLegendItems = 0)
        self.removeMarkers()
        self.tips.removeAll()
        
        self.xData = []
        self.yData = []
        edgesCount = 0
        
        # draw edges
        for e in range(self.nEdges):
            (key,i,j) = self.edges[e]
            
            x1 = self.visualizer.xCoors[i]
            x2 = self.visualizer.xCoors[j]
            y1 = self.visualizer.yCoors[i]
            y2 = self.visualizer.yCoors[j]
            
            fillColor = Qt.blue#self.discPalette[classValueIndices[self.rawdata[i].getclass().value], 255*insideData[j]]
            edgeColor = Qt.blue#self.discPalette[classValueIndices[self.rawdata[i].getclass().value]]

            #key = self.addCurve(str(e), fillColor, edgeColor, 0, style = QwtCurve.Lines, xData = [x1, x2], yData = [y1, y2])
            #self.edges[e] = (key,i,j)
            self.xData.append(x1)
            self.xData.append(x2)
            self.yData.append(y1)
            self.yData.append(y2)
                        
            self.edges[e] = (edgesCount,i,j)
            edgesCount += 1
        
        edgesCurveObject = UnconnectedLinesCurve(self, QPen(QColor(224,224,224)), self.xData, self.yData)
        self.edgesKey = self.insertCurve(edgesCurveObject)
        
        # draw vertices
        for v in range(self.nVertices):
            x1 = self.visualizer.xCoors[v]
            y1 = self.visualizer.yCoors[v]
            
            if self.colorIndex != -1:
                if self.visualizer.graph.items.domain[self.colorIndex].varType == orange.VarTypes.Continuous:
                    newColor = self.contPalette[self.noJitteringScaledData[self.colorIndex][v]]
                elif self.visualizer.graph.items.domain[self.colorIndex].varType == orange.VarTypes.Discrete:
                    newColor = self.discPalette[self.colorIndices[self.visualizer.graph.items[v][self.colorIndex].value]]
            else: 
                newColor = Qt.red #QColor(0,0,0)
            
            if v in self.selection:
                edgeColor = Qt.green;
                fillColor = Qt.green;
            else:
                fillColor = newColor
                edgeColor = newColor

            key = self.addCurve(str(v), fillColor, edgeColor, 6, xData = [x1], yData = [y1])
            self.vertices[v] = key
            self.indexPairs[key] = v
        
        # drew markers
        if len(self.labelText) > 0:
            for v in range(self.nVertices):
                x1 = self.visualizer.xCoors[v]
                y1 = self.visualizer.yCoors[v]
                lbl = ""
                for ndx in self.labelText:
                    values = self.visualizer.graph.items[v]
                    lbl = lbl + str(values[ndx]) + " "
        
                if lbl != '':
                    mkey = self.insertMarker(lbl)
                    self.marker(mkey).setXValue(float(x1))
                    self.marker(mkey).setYValue(float(y1))
                    self.marker(mkey).setLabelAlignment(Qt.AlignCenter + Qt.AlignBottom)            
        
        # add ToolTips
        self.tooltipData = []
        if len(self.tooltipText) > 0:
            for v in range(self.nVertices):
                x1 = self.visualizer.xCoors[v]
                y1 = self.visualizer.yCoors[v]
                lbl = ""
                for ndx in self.tooltipText:
                    values = self.visualizer.graph.items[v]
                    lbl = lbl + str(values[ndx]) + "\n"
        
                if lbl != '':
                    lbl = lbl[:-1]
                    self.tips.addToolTip(x1, y1, lbl)
            
    def setVertexColor(self, attribute):
        if attribute == "(one color)":
            self.colorIndex = -1
        else:
            i = 0
            for var in self.visualizer.graph.items.domain.variables:
                if var.name == attribute:
                    self.colorIndex = i
                    if var.varType == orange.VarTypes.Discrete: 
                        self.colorIndices = getVariableValueIndices(self.visualizer.graph.items, self.colorIndex)
                i += 1
        pass
        
    def setLabelText(self, attributes):
        self.labelText = []
        if isinstance(self.visualizer.graph.items, orange.ExampleTable):
            data = self.visualizer.graph.items
            for att in attributes:
                for i in range(len(data.domain)):
                    if data.domain[i].name == att:
                        self.labelText.append(i)
                        
                if self.visualizer.graph.items.domain.hasmeta(att):
                        self.labelText.append(self.visualizer.graph.items.domain.metaid(att))
    
    def setTooltipText(self, attributes):
        self.tooltipText = []
        if isinstance(self.visualizer.graph.items, orange.ExampleTable):
            data = self.visualizer.graph.items
            for att in attributes:
                for i in range(len(data.domain)):
                    if data.domain[i].name == att:
                        self.tooltipText.append(i)
                        
                if self.visualizer.graph.items.domain.hasmeta(att):
                        self.tooltipText.append(self.visualizer.graph.items.domain.metaid(att))
        
                            
    def edgesContainsEdge(self, i, j):
        for e in range(self.nEdges):
            (key,iTmp,jTmp) = self.edges[e]
            
            if (iTmp == i and jTmp == j) or (iTmp == j and jTmp == i):
                return True
        return False
        
    def addVisualizer(self, visualizer):
        self.visualizer = visualizer
        self.clear()
        
        self.nVertices = visualizer.graph.nVertices
        self.nEdges = 0
        self.vertexDegree = []
        
        #dodajanje vozlisc
        for v in range(0, self.nVertices):
            self.vertices[v] = None
            
        #dodajanje povezav
        
        for i in range(0, self.nVertices):
            for j in range(0, self.nVertices):
                try: 
                    if visualizer.graph[i,j] > 0:
                        if not self.edgesContainsEdge(i,j):
                            self.edges[self.nEdges] = (None,i,j)
                            self.nEdges += 1
                except TypeError:
                    pass # `visualizer.graph[i,j]' does not exist
                else:
                    pass # `visualizer.graph[i,j]' exists             
    
    def resetValues(self):
        self.vertices={}
        self.edges={}
        self.indexPairs={}
        #self.xCoors = None
        #self.yCoors = None
        self.n = 0
    
    def updateCanvas(self): #, xCoors, yCoors):
        #self.xCoors = xCoors
        #self.yCoors = yCoors
        
        self.setAxisAutoScaled()

        #self.drawGraph(self.nVertices);
        self.updateData()
        self.replot()
        
        # preprecimo avtomatsko primikanje plota (kadar smo odmaknili neko skrajno tocko)
        self.setAxisFixedScale()    
    
    def setAxisAutoScaled(self):
        self.setAxisAutoScale(self.xBottom)
        self.setAxisAutoScale(self.yLeft)

    def setAxisFixedScale(self):
        self.setAxisScale(self.xBottom, self.axisScale(self.xBottom).lBound(), self.axisScale(self.xBottom).hBound())
        self.setAxisScale(self.yLeft, self.axisScale(self.yLeft).lBound(), self.axisScale(self.yLeft).hBound())
        