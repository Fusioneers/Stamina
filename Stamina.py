print("importing libraries...")
import cv2 as cv
import numpy as np
import time as t
import os
import ast
import threading as th
from scipy.interpolate import splprep, splev
from pathlib import Path
import colorsys
import sys

savePath = str(Path.home()) + "\\AppData\\Local\\Stamina"
# print(savePath)

# resize
# don't stop code when moving window
# fps on screen

print("importing config...")

import config

print("preparing...")

cp = "ColorPicker"
idle = "Idle"
lc = "LevelCreator"
play = "Play"

app_name = "Stamina"
app_vers = "v1.0.3 beta"
app_desc = app_name + " " + app_vers

cp_name = "ColorPicker"
cp_desc = app_name + " " + app_vers + " - " + cp_name

wa_name = "Working Area"
wa_desc = app_name + " " + app_vers + " - " + wa_name

ls_name = "Level Selection"
ls_desc = app_name + " " + app_vers + " - " + ls_name

helpText = """
List of commands:
Use any time:
Idle            Set mode to idle
Play            Start the main functionalities
ColorPicker     Start ColorPicker

Use in mode ColorPicker:
SELECT          Select color
                Syntax: select COLOR
                COLOR:      name of color
                            e. g.   red
SET             Manually set HSV-Values
                Syntax: set <hue=HUE_MIN,HUE_MAX> <saturation=SATURATION_MIN,SATURATION_MAX> <value=VALUE_MIN,VALUE_MAX>
                HUE_MIN:    minimum hue
                HUE_MAX:    maximum hue
                ...
                
Need more help?
https://www.stamina.dev/help
"""

coordinates = {}
menuIsOpen = False
frames = 0
startTime = t.time()
lastTime = t.time()
lastImg = []
frames = 0
mousePosition = None


def getDict(path):
    file = open(path, "r")
    string = file.read()
    file.close()
    dict = ast.literal_eval(string)
    return dict


class Boss(th.Thread):
    mode = idle
    Ragnarok = False


class Data(th.Thread):
    Logo = cv.imread('resources/media/logos/staminaLogo.png')
    rezLogo = cv.resize(Logo, (config.windowSize[0], config.windowSize[1]))
    colors = getDict(config.colorsPath)
    bpc = getDict(config.body_parts_colors_path)
    defCol = getDict(config.defined_colors_path)

    allCats = {}
    allCatsList = []
    cats = os.listdir(config.challengesPath)

    categoryName = ""
    levelName = ""

    for cat in cats:
        finalCat = {"name": cat}
        finalCatList = [cat]
        for lvl in os.listdir(config.challengesPath + "\\" + cat):
            lvlData = getDict(config.challengesPath + "\\" + cat + "\\" + lvl)
            finalCat.update({lvl: lvlData})
            finalCatList.append(lvl)
        allCats.update({cat: finalCat})
        allCatsList.append(finalCatList)
    finalCats = allCats

    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        resetLevel()
        while not Boss.Ragnarok:
            if Boss.mode == play:
                if not cv.getWindowProperty(ls_desc, cv.WND_PROP_VISIBLE):
                    cv.namedWindow(ls_desc)
                    cv.resizeWindow(ls_desc, config.levelSelectionWidth, 75)
                    cv.createTrackbar("Category", ls_desc, 0, len(Data.allCatsList) - 1, empty)

                if not cv.getWindowProperty(wa_desc, cv.WND_PROP_VISIBLE):
                    cv.namedWindow(wa_desc)
                    cv.resizeWindow(wa_desc, config.workingAreaSelectionWidth, 160)
                    cv.createTrackbar("left", wa_desc, 0, 100, empty)
                    cv.createTrackbar("top", wa_desc, 0, 100, empty)
                    cv.createTrackbar("right", wa_desc, 100, 100, empty)
                    cv.createTrackbar("bottom", wa_desc, 100, 100, empty)

                if cv.getWindowProperty(wa_desc, cv.WND_PROP_VISIBLE):
                    config.workingArea["x0"] = cv.getTrackbarPos("left", wa_desc)
                    config.workingArea["y0"] = cv.getTrackbarPos("top", wa_desc)
                    config.workingArea["x1"] = cv.getTrackbarPos("right", wa_desc)
                    config.workingArea["y1"] = cv.getTrackbarPos("bottom", wa_desc)

                if cv.getWindowProperty(ls_desc, cv.WND_PROP_VISIBLE):
                    if Data.category != cv.getTrackbarPos("Category", ls_desc):
                        Data.category = cv.getTrackbarPos("Category", ls_desc)
                        Data.categoryName = Data.allCatsList[Data.category][0]
                        cv.createTrackbar("Level", ls_desc, 0, len(Data.allCatsList[Data.category]) - 2,
                                          empty)

                    if Data.level != cv.getTrackbarPos("Level", ls_desc):
                        Play.levelIsReady = False
                        Data.level = cv.getTrackbarPos("Level", ls_desc)
                        Data.levelName = Data.allCatsList[Data.category][Data.level + 1]

                if cv.waitKey(1) & 0xFF == ord("f"):
                    break

            if not Boss.mode == play:
                if cv.getWindowProperty(ls_desc, cv.WND_PROP_VISIBLE):
                    cv.destroyWindow(ls_desc)
                if cv.getWindowProperty(wa_desc, cv.WND_PROP_VISIBLE):
                    cv.destroyWindow(wa_desc)

            t.sleep(config.coolDownTime)


class Play(th.Thread):
    levelIsReady = False
    wpFactor = 0

    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        while not Boss.Ragnarok:
            if Boss.mode == play:
                if not Play.levelIsReady and not Data.categoryName == "" and not Data.levelName == "":
                    Play.coordinates = {}
                    Play.levelProgress = {}
                    Play.curves = {}
                    Play.WpNums = {}
                    Play.Wps = {}
                    Play.partScores = {}
                    Play.score = 0
                    Play.minScore = 0
                    Play.level = Data.finalCats[Data.categoryName][Data.levelName]
                    colorsList = getColorsList(len(Play.level))
                    i = 0
                    for part in Play.level["parts"]:
                        Play.levelProgress.update({part: {"waypointsDone": 0}})
                        Play.coordinates.update({part: [[], []]})
                        Play.partScores.update({part: 0})
                        Play.level["parts"][part].update({"wpColor": colorsList[0][i]})
                        i += 1
                        Play.Wps.update({part: {}})
                    Play.levelIsReady = True

                if Play.levelIsReady:
                    waX = (config.workingArea["x0"] - config.workingArea["x1"]) * config.windowSize[0]
                    waY = (config.workingArea["y0"] - config.workingArea["y1"]) * config.windowSize[1]
                    waA = waX * waY

                    if waA < 0:
                        waA = waA * -1

                    Play.wpFactor = np.sqrt(waA / 3.1416) / 100

                    for part in Play.level["parts"]:
                        tol = Play.level["parts"][part]["wpTolerance"] * Play.wpFactor / 100

                        if tol == 0:
                            tol = 0.01

                        Play.Wps[part].update({"wpTolerance": tol})

                        newx, newy, newsize = getCoordinates(Play.level["parts"][part])

                        xlist = Play.coordinates[part][0]
                        ylist = Play.coordinates[part][1]
                        Play.WpNums.update(
                            {part: Play.levelProgress[part]["waypointsDone"] % len(
                                Play.level["parts"][part]["waypoints"])})

                        relativeWp = Play.level["parts"][part]["waypoints"][Play.WpNums[part]]

                        Play.Wps[part].update({"crds": makeCrds(relativeWp)})

                        if newx != False and newy != False:
                            if len(xlist) == 0 or xlist[-1] != newx or ylist[-1] != newy:
                                if len(xlist) >= config.usePlots:
                                    if newx != False:
                                        xlist = xlist[1:]
                                    if newy != False:
                                        ylist = ylist[1:]

                                xlist.append(newx)
                                ylist.append(newy)

                            Play.coordinates.update({part: [xlist, ylist]})
                            if len(xlist) > 3:
                                curve = makeCurve([xlist, ylist])
                                Play.curves.update({part: curve})
                                if on_point(curve, Play.Wps[part]["crds"], Play.Wps[part]["wpTolerance"]):
                                    Play.levelProgress[part]["waypointsDone"] += 1
                                    Play.coordinates.update({part: [[newx], [newy]]})

                        Play.partScores.update(
                            {part: Play.levelProgress[part]["waypointsDone"] // len(
                                Play.level["parts"][part]["waypoints"])})

                    if not Play.minScore:
                        Play.minScore = Play.partScores[part]

                    elif Play.partScores[part] < Play.minScore:
                        Play.minScore = Play.partScores[part]

                    Play.score = makeScore()


            else:
                t.sleep(0.01)

            t.sleep(config.coolDownTime)


class GetImg(th.Thread):
    frames = 0

    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        capture = cv.VideoCapture()
        if config.dshow:
            capture_add = cv.CAP_DSHOW
        else:
            capture_add = 0

        capture.open(config.camera_port + capture_add)
        capture.set(cv.CAP_PROP_FPS, config.fps)
        capture.set(cv.CAP_PROP_FRAME_WIDTH, config.windowSize[0])
        capture.set(cv.CAP_PROP_FRAME_HEIGHT, config.windowSize[1])

        while not Boss.Ragnarok:
            st = t.time()
            GetImg.frames += 1
            _, i = capture.read()
            if config.mirrorMode:
                GetImg.img = cv.flip(i, 1)
            else:
                GetImg.img = i

            # print(imgIn.avFPS)

            GetImg.imHSV = cv.cvtColor(GetImg.img, cv.COLOR_RGB2HSV)
            FinishedImageCalculation.startImg = GetImg.img

            cv.waitKey(1)

            # try:
            #    print("FPS_CAM: " + str(1/(t.time()-st)))
            # except ZeroDivisionError:
            #    pass


class FinishedImageCalculation(th.Thread):
    # cv.namedWindow(title)

    # cv.imshow(title, img)

    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        while not Boss.Ragnarok:

            try:
                updateButtonsDict()

                if Boss.mode == play:
                    # print(Boss.mode)
                    i.i = i.startImg

                    putWorkingArea()

                    if config.showInfo:
                        putLevelInfo()

                    if Play.levelIsReady:
                        if config.showWaypoints:
                            putWaypoints()

                        if config.showCapturedPoints:
                            putCapturedPoints()

                        if config.showCurvePoints:
                            putCurves()

                        if config.showCheckedPoints:
                            putCheckedPoints()

                elif Boss.mode == cp:

                    i.i = cv.hconcat([i.startImg, Data.rezLogo])
                    lower = cv.hconcat([ColorPicker.showMask, ColorPicker.final])
                    i.i = cv.vconcat([i.i, lower])

                elif Boss.mode == lc:
                    pass

                elif Boss.mode == idle:
                    i.i = i.startImg

                i.i = cv.resize(i.i, (config.windowSize[0], config.windowSize[1]), interpolation=cv.INTER_AREA)
                putModeButtons()

                i.final = i.i
                # cv.imshow("test", i.final)

                if cv.waitKey(1) and 0xFF == ord("q"):
                    break

            except AttributeError as ex:
                # print(ex)
                # cv.imshow(app_desc, Data.rezLogo)
                if cv.waitKey(1) and 0xFF == ord("q"):
                    break
                pass

            except KeyError as ex:
                # print(ex)
                # cv.imshow(app_desc, Data.rezLogo)
                if cv.waitKey(1) and 0xFF == ord("q"):
                    break
                pass

            t.sleep(config.coolDownTime)


class GUI(th.Thread):
    reactClick = True

    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        while not Boss.Ragnarok:
            # if mousePosition != None and mousePosition["y"] >= config.txtOffset:
            #     txt = "x: " + str(mousePosition["x"]) + " y: " + str(mousePosition["y"])
            #     cv.putText(i.i, txt,
            #                (mousePosition["x"] + config.txtOffset, mousePosition["y"] - config.txtOffset),
            #                config.font, config.textSize, config.textColor, config.textThickness)

            try:
                cv.imshow(app_desc, i.final)
                cv.setMouseCallback(app_desc, mouse)
                cv.waitKey(1)

                if not cv.getWindowProperty(app_desc, cv.WND_PROP_VISIBLE):
                    Boss.Ragnarok = True

            except AttributeError as ex:
                # print(ex)
                t.sleep(0.01)

            t.sleep(config.coolDownTime)


class ColorPicker(th.Thread):
    standardValues = {'hue_min': '0', 'hue_max': '179', 'value_min': '0', 'value_max': '255', 'saturation_min': '0',
                      'saturation_max': '255'}

    ColorSelected = False
    ColorChanged = False

    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        while not Boss.Ragnarok:
            if Boss.mode == cp:
                if ColorPicker.ColorSelected:
                    if not cv.getWindowProperty(cp_desc, cv.WND_PROP_VISIBLE):
                        setMode(idle)
                    hue_min = cv.getTrackbarPos("HUE MIN", cp_desc)
                    hue_max = cv.getTrackbarPos("HUE MAX", cp_desc)
                    saturation_min = cv.getTrackbarPos("SATURATION MIN", cp_desc)
                    saturation_max = cv.getTrackbarPos("SATURATION MAX", cp_desc)
                    value_min = cv.getTrackbarPos("VALUE MIN", cp_desc)
                    value_max = cv.getTrackbarPos("VALUE MAX", cp_desc)
                    Data.colors.update({ColorPicker.color: {"hue_min": hue_min, "hue_max": hue_max,
                                                            "saturation_min": saturation_min,
                                                            "saturation_max": saturation_max,
                                                            "value_min": value_min, "value_max": value_max}})
                    lower = np.array([hue_min, saturation_min, value_min])
                    upper = np.array([hue_max, saturation_max, value_max])
                    ColorPicker.startHSV = imgIn.imHSV
                    ColorPicker.imgIn = imgIn.img
                    ColorPicker.mask = cv.inRange(ColorPicker.startHSV, lower, upper)
                    blank_image = np.zeros((config.windowSize[1], config.windowSize[0], 3), np.uint8)
                    blank_image[:, :] = config.cpMaskColor
                    ColorPicker.showMask = cv.bitwise_and(blank_image, blank_image, mask=ColorPicker.mask)
                    ColorPicker.final = cv.bitwise_and(ColorPicker.imgIn, ColorPicker.imgIn, mask=ColorPicker.mask)
                    cv.waitKey(1)
                else:
                    blank_image = np.zeros((config.windowSize[1], config.windowSize[0], 3), np.uint8)
                    blank_image[:, :] = config.cpMaskColor
                    ColorPicker.showMask = blank_image
                    ColorPicker.final = imgIn.img
                if ColorPicker.ColorChanged:
                    try:
                        openPicker(Data.colors[ColorPicker.color])
                    except Exception:
                        openPicker()
                    ColorPicker.ColorChanged = False
                    ColorPicker.ColorSelected = True

            else:
                t.sleep(0.01)
            t.sleep(config.coolDownTime)

    def save():
        colorFile = open(config.colorsPath, "w")
        colorFile.write(str(Data.colors))
        colorFile.close()
        print("colors successfully updated!\n")


class LevelCreator(th.Thread):  # COMING SOON

    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        while not Boss.Ragnarok:
            if Boss.mode == lc:
                LevelCreator.level = {}

                partdata = {}
                color = input("Color:       ")
                partdata.update({"color": color})

                level.update({partname: partdata})

                createPart = input("Create another part? 'y'/'n':  ")

            t.sleep(0.01)


class UserInputCmd(th.Thread):
    def __init__(self):
        th.Thread.__init__(self)

    def run(self):
        while not Boss.Ragnarok:
            try:
                uinput = input()
                splitted = uinput.rsplit(" ")
                cmd = splitted[0]

                if cmd == lc or cmd == "levelcreator" or cmd == "lc" or cmd == "LEVELCREATOR" or cmd == "LC" or cmd == "L" or cmd == "l":
                    setMode(lc)
                elif cmd == play or cmd == "play" or cmd == "pl" or cmd == "p" or cmd == "PLAY" or cmd == "PL" or cmd == "P":
                    setMode(play)
                elif cmd == cp or cmd == "colorpicker" or cmd == "cp" or cmd == "c" or cmd == "CP" or cmd == "C" or cmd == "COLORPICKER":
                    setMode(cp)
                elif cmd == idle or cmd == "idle" or cmd == "id" or cmd == "i" or cmd == "ID" or cmd == "I" or cmd == "IDLE":
                    setMode(idle)
                elif cmd == "exit" or cmd == "EXIT":
                    Boss.Ragnarok = True
                elif cmd == "HELP" or cmd == "help" or cmd == "h" or cmd == "H":
                    print(helpText)

                else:
                    if Boss.mode == idle:
                        pass

                    elif Boss.mode == lc:
                        if cmd == "set":
                            if len(splitted) > 1:
                                args = splitted[1:]
                                for arg in args:
                                    argsplitted = arg.rsplit("=")
                                    value = argsplitted[0]
                                    if value == "c" or value == "cat" or value == "category":
                                        LevelCreator.level.update({"category": value})
                                    elif value == "n" or value == "levelname" or value == "name" or value == "LevelName" or value == "Name":
                                        LevelCreator.level.update({"name": value})
                                    else:
                                        print("SYNTAX ERROR")
                        elif cmd == "":
                            pass

                    elif Boss.mode == cp:
                        if cmd == "save" or cmd == "s":
                            ColorPicker.save()
                        # elif cmd == "reset" or cmd == "r":
                        #    ColorPicker.reset()
                        elif cmd == "cancel" or cmd == "c":
                            setMode(idle)
                        elif cmd == "select" or cmd == "sel":
                            if len(splitted) == 2:
                                ColorPicker.color = splitted[1]
                                ColorPicker.ColorSelected = False
                                ColorPicker.ColorChanged = True
                            else:
                                print("SYNTAX ERROR")
                        elif cmd == "set":
                            if len(splitted) > 1:
                                args = splitted[1:]
                                changes = {}
                                for arg in args:
                                    argsplitted = arg.rsplit("=")
                                    value = argsplitted[0]
                                    values = argsplitted[1].rsplit(",")
                                    if value == "h" or value == "hue":
                                        if values[0] != "*":
                                            changes.update({"hue_min": int(values[0])})
                                        if values[1] != "*":
                                            changes.update({"hue_max": int(values[1])})
                                    elif value == "s" or value == "saturation":
                                        if values[0] != "*":
                                            changes.update({"saturation_min": int(values[0])})
                                        if values[1] != "*":
                                            changes.update({"saturation_max": int(values[1])})
                                    elif value == "v" or value == "value":
                                        if values[0] != "*":
                                            changes.update({"value_min": int(values[0])})
                                        if values[1] != "*":
                                            changes.update({"value_max": int(values[1])})
                                    newColorDef = Data.colors[ColorPicker.color]
                                for change in changes:
                                    newColorDef.update({change: changes[change]})
                                openPicker(newColorDef)
                                print(Data.colors)
                            else:
                                print("SYNTAX ERROR")

                    elif Boss.mode == play:
                        pass

            except Exception:
                pass


def updateButtonsDict():
    rowHeight = config.buttonHeight + config.buttonSpace
    buttonRow = 0
    buttonX = config.buttonSpace
    for button in Data.modes:
        # if Data.modes[button]["state"] == True:
        buttonWidth = Data.modes[button]["width"]
        if (buttonRow + 1) * rowHeight <= config.windowSize[1] * config.buttonPlace[1] / 100:
            if buttonX + config.buttonSpace + buttonWidth > config.windowSize[0] * config.buttonPlace[0] / 100:
                buttonRow = buttonRow + 1
                buttonX = config.buttonSpace

            x0 = buttonX
            y0 = buttonRow * rowHeight + config.buttonSpace
            x1 = buttonX + buttonWidth
            y1 = buttonRow * rowHeight + config.buttonSpace + config.buttonHeight

            buttonX = x1 + config.buttonSpace

            Data.modes[button].update({"x0": x0})
            Data.modes[button].update({"y0": y0})
            Data.modes[button].update({"x1": x1})
            Data.modes[button].update({"y1": y1})


def empty(a):
    pass


def mouse(event, x, y, flags, params):
    if event == cv.EVENT_LBUTTONDOWN:
        if GUI.reactClick:
            # print("========================MOUSE========================  " + str([x, y]))
            for button in Data.modes:
                if Data.modes[button]["x0"] < x < Data.modes[button]["x1"] and Data.modes[button]["y0"] < y < \
                        Data.modes[button]["y1"]:
                    setMode(button)
    else:
        GUI.reactClick = True


def getCoordinates(part):
    colordata = Data.colors[Data.bpc[part["body_part"]]["markerColor"]]
    # partName = part["name"]
    lower = np.array([colordata["hue_min"], colordata["saturation_min"], colordata["value_min"]])
    upper = np.array([colordata["hue_max"], colordata["saturation_max"], colordata["value_max"]])
    mask = cv.inRange(imgIn.imHSV, lower, upper)
    # fin = cv.bitwise_and(i.i, i.i, mask=mask)
    contours, hierarchy = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    xmid, ymid, area = False, False, False

    if config.test == 0:
        if len(contours) >= config.numberOfBigAreas:
            xlist = []
            ylist = []
            contours.sort(key=cv.contourArea, reverse=True)
            for n in range(config.numberOfBigAreas):
                cnt = contours[n]
                area = cv.contourArea(cnt)
                if area > config.min_area:
                    peri = cv.arcLength(cnt, True)
                    ax = cv.approxPolyDP(cnt, 0.02 * peri, True)
                    x, y, w, h = cv.boundingRect(ax)
                    xlist.append(x + w / 2)
                    ylist.append(y + h / 2)

                    xmid = int(sum(xlist) / len(xlist))
                    ymid = int(sum(ylist) / len(ylist))
    elif config.test == 1:
        xlist = []
        ylist = []
        for cnt in contours:
            area = cv.contourArea(cnt)
            if area > config.min_area:
                peri = cv.arcLength(cnt, True)
                ax = cv.approxPolyDP(cnt, 0.02 * peri, True)
                x, y, w, h = cv.boundingRect(ax)
                xlist.append(x + w / 2)
                ylist.append(y + h / 2)

                xmid = int(sum(xlist) / len(xlist))
                ymid = int(sum(ylist) / len(ylist))
    elif config.test == 3:
        if len(contours) >= 1:
            for cnt in contours:
                pass

    # print(coordinates)
    return [xmid, ymid, area]


def openPicker(colorDef=False):
    cv.namedWindow(cp_desc)
    cv.resizeWindow(cp_desc, config.cpWidth, 320)
    if not colorDef:
        cv.createTrackbar("HUE MIN", cp_desc, 0, 179, empty)
        cv.createTrackbar("HUE MAX", cp_desc, 179, 179, empty)
        cv.createTrackbar("SATURATION MIN", cp_desc, 0, 255, empty)
        cv.createTrackbar("SATURATION MAX", cp_desc, 255, 255, empty)
        cv.createTrackbar("VALUE MIN", cp_desc, 0, 255, empty)
        cv.createTrackbar("VALUE MAX", cp_desc, 255, 255, empty)
    else:
        cv.createTrackbar("HUE MIN", cp_desc, colorDef["hue_min"], 179, empty)
        cv.createTrackbar("HUE MAX", cp_desc, colorDef["hue_max"], 179, empty)
        cv.createTrackbar("SATURATION MIN", cp_desc, colorDef["saturation_min"], 255, empty)
        cv.createTrackbar("SATURATION MAX", cp_desc, colorDef["saturation_max"], 255, empty)
        cv.createTrackbar("VALUE MIN", cp_desc, colorDef["value_min"], 255, empty)
        cv.createTrackbar("VALUE MAX", cp_desc, colorDef["value_max"], 255, empty)


def clearButtons():
    for button in buttons.dict:
        buttons.dict[button]["state"] = False


def openMenu():
    # show menu buttons
    clearButtons()
    buttons.dict["closeMenu"]["state"] = True
    buttons.dict["openPickerMenu"]["state"] = True


def closeMenu():
    clearButtons()
    buttons.dict["openMenu"]["state"] = True


def putWorkingArea():
    cv.rectangle(i.i, (int(config.workingArea["x0"] * config.windowSize[0] / 100),
                       int(config.workingArea["y0"] * config.windowSize[1] / 100)), (
                     int(config.workingArea["x1"] * config.windowSize[0] / 100) - 1,
                     int(config.workingArea["y1"] * config.windowSize[1] / 100) - 1), config.workingAreaColor,
                 config.workingAreaThickness)


def putModeButtons():
    for button in Data.modes:
        if Data.modes[button]["state"] == True:
            i.i[Data.modes[button]["y0"]:Data.modes[button]["y1"],
            Data.modes[button]["x0"]:Data.modes[button]["x1"]] = config.selectedModeButtonColor  # 0y, 1y, 0x, 1x
            cv.putText(i.i, Data.modes[button]["label"],
                       (Data.modes[button]["x0"] + config.txtOffset, Data.modes[button]["y1"] - config.txtOffset),
                       config.font, config.textSize, config.textColor, config.textThickness)
        else:
            i.i[Data.modes[button]["y0"]:Data.modes[button]["y1"],
            Data.modes[button]["x0"]:Data.modes[button]["x1"]] = config.unselectedModeButtonColor  # 0y, 1y, 0x, 1x
            cv.putText(i.i, Data.modes[button]["label"],
                       (Data.modes[button]["x0"] + config.txtOffset, Data.modes[button]["y1"] - config.txtOffset),
                       config.font, config.textSize, config.textColor, config.textThickness)


def putWaypoints():
    try:
        if Play.levelIsReady != False:
            if len(Play.Wps) > 0:
                for part in Play.Wps:
                    r = int(Play.Wps[part]["wpTolerance"])
                    x, y = Play.Wps[part]["crds"]
                    wpColor = Data.defCol[Data.bpc[Play.level["parts"][part]["body_part"]]["displayColor"]]
                    cv.circle(i.i, (x, y), r, wpColor, config.waypointThickness)
                    txtColor = invertRGB(wpColor)
                    cv.putText(i.i, str(Play.partScores[part]), (int(x - 0.5 * r), int(y + 0.5 * r)), config.font, 3,
                               txtColor, 3)


    except RuntimeError as ex:
        pass


def putCapturedPoints():
    try:
        if len(Play.coordinates) > 0:
            for part in Play.coordinates:
                for n in range(len(Play.coordinates[part][0])):
                    cv.circle(i.i, (Play.coordinates[part][0][n], Play.coordinates[part][1][n]),
                              config.capturedPointSize, config.capturedPointColor, config.capturedPointThickness)
    except Exception:
        pass


def putCurves():
    try:
        curves = Play.curves
        if len(curves) > 0:
            for part in curves:
                pointColor = Data.defCol[Data.bpc[Play.level["parts"][part]["body_part"]]["displayColor"]]
                if len(curves[part][0]) > 0:
                    for n in range(len(curves[part][0])):
                        cv.circle(i.i, (int(curves[part][0][n]), int(curves[part][1][n])),
                                  config.curvePointSize + config.curveLineSize,
                                  config.curveLineColor, config.curvePointThickness)
                    for n in range(len(curves[part][0])):
                        cv.circle(i.i, (int(curves[part][0][n]), int(curves[part][1][n])), config.curvePointSize,
                                  pointColor, config.curvePointThickness)
    except RuntimeError as ex:
        pass


def putCheckedPoints():
    pass


def putLevelInfo():
    levelDesc = Play.level["category"] + " | " + Play.level["name"] + " | score: " + str(Play.score)
    cv.putText(i.i, levelDesc, (int(config.windowSize[0] * config.levelDescIndent / 100), 20), config.font,
               config.textSize, config.textColor,
               config.textThickness)
    try:
        cv.putText(i.i, Play.level["description"], (int(config.windowSize[0] * config.levelDescIndent / 100), 40),
                   config.font, config.textSize, config.textColor,
                   config.textThickness)
    except Exception:
        pass


def makeCrds(prop_in_wa):
    x = config.workingArea["x0"] * config.windowSize[0] / 100 + (
            config.workingArea["x1"] - config.workingArea["x0"]) / 10000 * prop_in_wa[0] * config.windowSize[0]
    y = config.workingArea["y0"] * config.windowSize[1] / 100 + (
            config.workingArea["y1"] - config.workingArea["y0"]) / 10000 * prop_in_wa[1] * config.windowSize[1]
    return [int(x), int(y)]


def openPickerMenu():
    clearButtons()
    for color in Data.colors:
        buttons.dict[color]["state"] = True


def calibrateColor(color):
    global pickerActive
    pickerActive = True
    global colorToCalibrate
    colorToCalibrate = color


def getMotion(org, lastImg):
    lastGray = cv.cvtColor(lastImg, cv.COLOR_BGR2GRAY)
    imgGray = cv.cvtColor(org, cv.COLOR_BGR2GRAY)

    lastBlur = cv.GaussianBlur(lastGray, (21, 21), 0)
    imgBlur = cv.GaussianBlur(imgGray, (21, 21), 0)
    imgDiff = cv.absdiff(lastBlur, imgBlur)


def printInfo():
    print(coordinates)
    global currentTime, lastTime
    print("FRAMES:  (progressed)", frames)
    currentTime = t.time() - startTime
    print("TIME:    (progressed)", currentTime)
    averageFPS = frames / currentTime
    print("avg. FPS (progressed):", averageFPS)
    currentFPS = 1 / (currentTime - lastTime)
    print("cur. FPS (progressed):", currentFPS)

    print("FRAMES:  ", imgIn.frames)
    currentTime = t.time() - startTime
    print("TIME:    ", currentTime)
    averageFPS = imgIn.frames / currentTime
    print("avg. FPS:", averageFPS)
    currentFPS = 1 / (currentTime - lastTime)
    print("cur. FPS:", currentFPS)

    info = "frames: " + str(frames) + "\ntime: " + str(currentTime) + "\navg. FPS: " + str(
        averageFPS) + "\ncur. FPS: " + str(currentFPS)
    # cv.putText(i.i, info,
    #           (config.txtOffset, imgHeight - config.txtOffset), config.font, config.textSize,
    #           config.textColor, config.textThickness)

    lastTime = currentTime


def on_point(curve, waypoint, tolerance=10):
    rt = False
    for n in range(config.newPlots):  # config.newPlts - config.newPlts // config.usePlts, config.newPlts):
        if np.sqrt((curve[0][n] - waypoint[0]) ** 2 + (curve[1][n] - waypoint[1]) ** 2) <= tolerance:  # tolerance:
            rt = True
    return rt


def makeCurve(crds):
    # st = t.time()
    # print(crds, waypoint)
    tck, u = splprep(crds, s=0)
    # print(tck, u)
    u_new = np.linspace(u.min(), u.max(), config.newPlots)
    # print(u_new)
    nowCurve = splev(u_new, tck)
    # print(nowCurve)
    # print("isOnPoint Time: " + str(t.time()-st))
    return nowCurve


def makeScore():
    min = -1
    for part in Play.partScores:
        if min == -1:
            min = Play.partScores[part]
        elif min > Play.partScores[part]:
            min = Play.partScores[part]
    return min


def getColorsList(n):
    colors = []
    hue = []
    for p in range(n):
        o = int(360 / n * (p + 1) - 1)
        hue.append(o)
        RGB_color = tuple(round(i * 255) for i in colorsys.hsv_to_rgb(o / 360, 1, 1))
        colors.append(RGB_color)
    return colors, hue


def setMode(mode, args=[]):
    modeToKill = Boss.mode
    Boss.mode = mode
    t.sleep(0.01)
    if modeToKill == idle:
        pass
    elif modeToKill == play:
        resetLevel()
        Play.levelIsReady = False
    elif modeToKill == cp:
        cv.destroyWindow(cp_desc)
        ColorPicker.ColorSelected = False
    elif modeToKill == lc:
        pass

    for oneMode in Data.modes:
        Data.modes[oneMode].update({"state": False})
    Data.modes[mode].update({"state": True})
    print("Mode selected: " + str(mode))


def resetLevel():
    Play.levelIsReady = False
    Data.level = -1
    Data.category = -1
    Data.categoryName = ""
    Data.levelName = ""


def invertRGB(inp):
    return (255 - inp[0],
            255 - inp[1],
            255 - inp[2])


Data.modes = {
    play: {
        "state": False,
        "label": play
    },
    cp: {
        "state": False,
        "label": cp
    },
    #    lc: {
    #        "state": False,
    #        "label": lc
    #    },
    idle: {
        "state": True,
        "label": idle
    }
}

for mode in Data.modes:
    Data.modes[mode].update({"width": len(Data.modes[mode]["label"]) * 10})

imgIn = GetImg()
gui = GUI()
# buttonsTh = buttons()
dataTh = Data()
i = FinishedImageCalculation()
p = Play()
cp_thread = ColorPicker()
lc_thread = LevelCreator()
ui = UserInputCmd()

imgIn.daemon = True
gui.daemon = True
dataTh.daemon = True
i.daemon = True
p.daemon = True
cp_thread.daemon = True
lc_thread.daemon = True
ui.daemon = True

print("starting threads...")

imgIn.start()
gui.start()
dataTh.start()
p.start()
i.start()
cp_thread.start()
lc_thread.start()
ui.start()

print("\nWelcome to Stamina!\nhttps://www.stamina.dev/\n")

while not Boss.Ragnarok:
    t.sleep(0.01)

sys.exit()

# debug
