__author__ = 'thornag'

from PyQt4 import QtCore, QtGui
import model

import di

class Level:
    __mapIndex=0
    __view=None
    __id=None
    def __init__(self, mapIndex):
        self.__mapIndex=mapIndex

    def getMapIndex(self):
        return self.__mapIndex

    def setView(self, view):
        self.__view = view
        view.setModel(self)

    def getView(self):
        return self.__view

    def setId(self, id_):
        self.__id = str(id_)

    def getId(self):
        return self.__id

class Link:
    __view=None
    __left=None
    __right=None
    __id=None

    def replaceRoomPointer(self, oldRoom, newRoom):
        if oldRoom.getId() == self.__left[0].getId():
            self.setLeft(newRoom, self.__left[1], self.__left[2])
        if oldRoom.getId() == self.__right[0].getId():
            self.setRight(newRoom, self.__right[1], self.__right[2])

    def setId(self, id_):
        self.__id = str(id_)

    def getId(self):
        return self.__id

    def setView(self, view):
        self.__view = view
        view.setModel(self)

    def getView(self):
        return self.__view

    def setLeft(self, room, exit_, label):
        self.__left = (room, exit_, str(label) if not label==None else label)

    def setRight(self, room, exit_, label):
        self.__right = (room, exit_, str(label) if not label==None else label)

    def getLeft(self):
        return self.__left

    def getRight(self):
        return self.__right

    def pointsAt(self, room):
        return self.__left[0].getId() == room.getId() or self.__right[0].getId() == room.getId()

    def getDestinationFor(self, room):
        if room.getId() == self.__left[0].getId():
            return self.__right[0]
        if room.getId() == self.__right[0].getId():
            return self.__left[0]

    def getDestinationSideFor(self, room):
        if room.getId() == self.__left[0].getId():
            return self.__right
        if room.getId() == self.__right[0].getId():
            return self.__left

    def getSourceSideFor(self, room):
        if room.getId() == self.__left[0].getId():
            return self.__left
        if room.getId() == self.__right[0].getId():
            return self.__right

    def replaceSourceSideFor(self, room, exit_, label):
        if room.getId() == self.__left[0].getId():
            self.__left = (room, exit_, str(label) if not label==None else label)
        if room.getId() == self.__right[0].getId():
            self.__right = (room, exit_, str(label) if not label==None else label)


    def isCustom(self): return False

class CustomLink(Link):
    def isCustom(self): return True

class Room:
    __exits=0
    __currentlyVisited=False
    __view=None
    __position=None
    __id=None
    __level=None
    __map=di.ComponentRequest('Map')
    __properties=None
    PROP_NAME='name'
    PROP_COMMANDS='commands'
    PROP_COLOR='color'
    PROP_CLASS='class'
    PROP_LABEL='label'
    def __init__(self, exits=0, properties=None):
        self.__exits = exits
        self.__links={}
        self.__customLinks=[]
        if properties is None: properties={}
        if self.PROP_NAME not in properties: properties[ self.PROP_NAME] = ''
        if self.PROP_COLOR not in properties: properties[ self.PROP_COLOR]=None
        if self.PROP_COMMANDS not in properties: properties[ self.PROP_COMMANDS]=''
        if self.PROP_CLASS not in properties: properties[ self.PROP_CLASS]=''
        if self.PROP_LABEL not in properties: properties[ self.PROP_LABEL]=''
        self.__properties=properties

    def hasMaskedExits(self):
        for index, link in self.__links.items():
            sourceSide=link.getSourceSideFor(self)
            if sourceSide[2] is not None and len(sourceSide[2]): return True

    def getMaskedExitsString(self):
        returnString=""
        for index, link in self.__links.items():
            sourceSide=link.getSourceSideFor(self)
            if sourceSide[2] is not None and len(sourceSide[2]):
                if sourceSide[1] == model.Direction.OTHER:
                    returnString += "exit:custom:%s\n" % sourceSide[2]
                else:
                    returnString += "exit:%s:%s\n" % (model.Direction.mapToLabel(sourceSide[1]), sourceSide[2])
        return returnString

    def properties(self):
        return self.__properties

    def getProperty(self, property):
        return self.__properties[property]

    def setProperty(self, property, value):
        self.__properties[property] = str(value)

    def position(self):
        return self.__position

    def deleteLink(self, link, iteration=False):
        if link.getView() and link.getView().scene(): link.getView().scene().removeItem(link.getView())
        leftRoom = link.getLeft()
        if not iteration or leftRoom[0].getId() is not self.getId():
            leftRoom[0].removeExit(leftRoom[1], leftRoom[2])
        rightRoom = link.getRight()
        if not iteration or rightRoom[0].getId() is not self.getId():
            rightRoom[0].removeExit(rightRoom[1], leftRoom[2])
        leftRoom[0].getView().update()
        rightRoom[0].getView().update()
        self.__map.removeLink(link)

    def delete(self):
        for linkPointer in self.__links:
            link = self.__links[linkPointer]
            if link.isCustom(): continue
            self.deleteLink(link, True)

        for link in self.__customLinks:
            self.deleteLink(link, True)

        self.__links={}
        self.__exits=0
        self.getView().scene().removeItem(self.getView())
        self.__map.removeRoom(self)

    def exits(self):
        return self.__exits

    def setId(self, id_):
        self.__id = str(id_)

    def getId(self):
        return self.__id

    def hasExit(self, exit_):
        return self.__exits & exit_ and exit_ in self.__links

    def addExit(self, exit_):
        self.__exits = self.__exits | exit_

    def removeExit(self, exit_, label=None):
        if exit_ == model.Direction.OTHER: return self.removeCustomLink(label)
        self.__exits = self.__exits ^ exit_
        if exit_ in self.__links:
            del self.__links[exit_]

    def removeCustomLink(self, label):
        for index, link in enumerate(self.__customLinks):
            thisRoomsLink = link.getSourceSideFor(self)
            if thisRoomsLink[2] == label:
                del self.__customLinks[index]
                break;
        if not len(self.__customLinks):
            self.__exits = self.__exits ^ model.Direction.OTHER
        if hasattr(self, '__links'):
            del self.__links[model.Direction.OTHER]


    def setCurrentlyVisited(self, bVisited):
        self.__currentlyVisited = bool(bVisited)

    def isCurrentlyVisited(self):
        return bool(self.__currentlyVisited)

    def setView(self, view):
        self.__view = view
        view.setModel(self)

    def getView(self):
        return self.__view

    def setPosition(self, QPoint):
        self.__position = QPoint
        self.__view.setPos(QtCore.QPointF(QPoint))

    def setPositionFromView(self):
        self.__position = self.__view.pos()

    def hasLinkAt(self, direction):
        return direction in self.__links

    def linkAt(self, direction):
        return self.__links[direction]

    def addLink(self, exit_, link):
        if isinstance(link, CustomLink): self.addCustomLink(link)
        self.__links[exit_] = link

    def addCustomLink(self, link):
        self.__customLinks.append(link)

    def getCustomLinks(self):
        return self.__customLinks

    def getLinks(self):
        return self.__links

    def getNonCustomLinks(self):
        links = self.__links
        if model.Direction.OTHER in links: del links[model.Direction.OTHER]
        return links

    def setLevel(self, level):
        self.__level = level

    def getLevel(self):
        return self.__level

    def getSettings(self):
        return self.properties()



