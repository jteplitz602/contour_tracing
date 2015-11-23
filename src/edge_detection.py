import cv2
import numpy as np
import sys
import os
import collections
import heapq
import math
from Queue import PriorityQueue
from matplotlib import pyplot as plt
edges = None
padding = 100
NUM_KNUCKLES = 3

# Rotates an image by the given angle (in radians) and returns the result
def rotateImage(img, angle):
    rows,cols,_ = img.shape
    M = cv2.getRotationMatrix2D((cols/2,rows/2), math.degrees(angle), 1)
    return cv2.warpAffine(img, M, (cols, rows))

def cropImage(img):
    global edges
    #gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    gray = img
    _,thresh = cv2.threshold(gray,70,255,cv2.THRESH_BINARY)
    contours = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnt = contours[0]
    edges = cnt
    x,y,w,h = cv2.boundingRect(cnt)

    (x1, y1) = map(lambda val: max(0, val - padding), (x, y))
    (x2, y2) = map(lambda val: val + padding, (x + w, y + h))

    x2 = min(len(cnt), x2)
    y2 = min(len(cnt[0]), y2)

    croppedImage = img[y1:y2, x1:x2]
    return croppedImage

# Converts image to grayscale and applys the given threshold
def applyThreshold(img, threshold):
    singleChannel = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(singleChannel,threshold,255,cv2.THRESH_BINARY)
    return thresh

def defuzzImage(img, iterations = 20, mode = cv2.MORPH_OPEN):
    kernel = np.ones((5,5),np.uint8)
    #NOTE: I just picked 5 iterations here because it seems to be the smallest number that works on a random picture of rishi's hand...
    return cv2.morphologyEx(img, mode, kernel, iterations=iterations)

# Returns an np array containing the xy points of the knuckles
def getKnuckles(img):
    _, contours0, hierarchy = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    # There could be multiple contours, so pick the largest one
    cnt = max(contours0, key=lambda x: len(x))
    print("Num contours", len(contours0))
    print("Size of biggest contour", len(cnt))
    hull = cv2.convexHull(cnt, returnPoints = False)
    defects = cv2.convexityDefects(cnt, hull)
    cutoff = len(img) * 0.9 # Only grab points from top 10% of image
    bottomDefects = []
    Defect = collections.namedtuple("Defect", "depth point")
    for i in range(defects.shape[0]):
        s,e,f,d = defects[i,0]
        start = tuple(cnt[s][0])
        end = tuple(cnt[e][0])
        far = tuple(cnt[f][0])
        if (far[1] >= cutoff):
            bottomDefects.append(Defect(depth = d / 256.0, point = far))

    defects = heapq.nlargest(NUM_KNUCKLES, bottomDefects, key=lambda defect: defect.depth)
    for defect in defects:
        cv2.circle(img,defect.point,5,[0,0,255],-1)

    return np.array(map(lambda defect: defect.point, defects))

def getOffsetAngle(img, knuckles):
    [vx,vy,x,y] = cv2.fitLine(knuckles, cv2.DIST_L2,0,0.01,0.01)
    rows,cols = img.shape
    lefty = (-x * vy / vx) + y
    righty = ((cols - x) * vy / vx) +y
    height = righty - lefty
    hypot = math.hypot(cols - 1, height)
    return math.asin(height / hypot)

def normalizeImage(img):
    thresh = applyThreshold(img, 10)
    knuckles = getKnuckles(thresh)
    angle = getOffsetAngle(thresh, knuckles)

    return rotateImage(img, angle)

def getContourPoints(cnt):
    points = []
    for x, vals in enumerate(cnt):
        for y,val in enumerate(vals):
            if val != 0:
                points.append([x,y])
    return np.array(points)

def findWristPoint(averages):
    if (len(averages) == 1):
        print("One size array")
        return 0
    elif (len(averages) == 2):
        print("Two size array")
        return 0 if averages[0] < averages[1] else 1
    else:
        mid = len(averages) / 2
        if (averages[mid] < averages[mid - 1]):
            if (averages[mid] < averages[mid + 1]):
                return mid
            else:
                # recurse on right half of array
                return mid + findWristPoint(averages[mid + 1:]) + 1
        else:
            # recurse on left half of array
            return findWristPoint(averages[:mid])

# TODO: Remove this method and compute averages in findWristPoint
def getThicknesses(img):
    WINDOW_SIZE = 10
    print("Length", len(img))
    averages = []
    for row in img:
        if (len(averages) < WINDOW_SIZE):
            averages.append(row.mean())
        else:
            sum = 0
            for i in range(len(averages) - WINDOW_SIZE, len(averages) - 1):
                sum += averages[i]
            sum += row.mean()
            averages.append(sum / WINDOW_SIZE)

        #averages.append(row.mean())
    return averages


def removeWrist(img):
    DOWNSAMPLE_AMOUNT = 2
    rows,cols,_ = img.shape
    defuzzedImg = defuzzImage(img)
    thresh = applyThreshold(defuzzedImg, 10)
    thresh = cv2.pyrDown(thresh, dstsize = (cols / DOWNSAMPLE_AMOUNT, rows / DOWNSAMPLE_AMOUNT))
    thicknesses = getThicknesses(thresh)
    wristPoint = findWristPoint(thicknesses)
    print("min", thicknesses[wristPoint], thicknesses[wristPoint + 1], thicknesses[wristPoint - 1])
    cv2.line(img, (0, wristPoint), (img.shape[1], wristPoint), [0, 255, 0], 5)
    return img

basePath = os.path.dirname(os.path.abspath(__file__ ))
path = basePath + "/../images/" + sys.argv[1]
img = cv2.imread(path)
background = cv2.imread(basePath + "/../images/empty_box.jpg")
bgRemoved = applyThreshold(background - img, 50)

plt.subplot(221),plt.imshow(img, cmap = 'gray')
plt.title('Original Image'), plt.xticks([]), plt.yticks([])
croppedImage = cropImage(bgRemoved)
#croppedImage = removeWrist(croppedImage)
#croppedImage = normalizeImage(croppedImage)
plt.subplot(222),plt.imshow(bgRemoved, cmap="gray")
plt.title("Bg Removed"),plt.xticks([]), plt.yticks([])
plt.subplot(223),plt.imshow(croppedImage,cmap = 'gray')
plt.title('Cropped Image'), plt.xticks([]), plt.yticks([])

plt.show()
