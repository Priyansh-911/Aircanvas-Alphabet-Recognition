import colorsys
import numpy as np
import cv2
import HTmodule as HTM
import os

class image_class():

    def __init__(self, overlayList):
        self.brushThickness = 15
        self.eraserSize = 50
        self.imgCanvas = np.zeros((720, 1280, 3), np.uint8)
        self.canvasClear = np.zeros((720, 1280, 3), np.uint8)
        self.drawColor = (51, 51, 225)
        self.header = overlayList[0]
        self.xp = 0
        self.yp = 0

        self.detector = HTM.handDetector(detectionCon=0.85)
    
    def generate_frame(self, img, overlayList):
        img = cv2.flip(img, 1)
    
        # find handLandmarks
        img = self.detector.findHands(img)
        lmList = self.detector.trackPos(img, draw=False)
        # print(lmList)
        
        if lmList != []:
            x1, y1 = lmList[8][1:]
            x2, y2 = lmList[12][1:]

            fingers = self.detector.fingerUp()

            if fingers[1] and fingers[2]:
                self.xp, self.yp = 0, 0

                if y1 < 125:
                    if 0 < x1< 125:
                        self.header = overlayList[0]
                        self.drawColor = (51, 51, 225)
                    
                    elif 250 < x1 < 400:
                        self.header = overlayList[1]
                        self.drawColor = (255, 60, 42)
                    
                    elif 550 < x1 < 700:
                        self.header = overlayList[2]
                        self.drawColor = (26, 255, 247)
                    
                    elif 850 < x1 < 1000:
                        self.header = overlayList[3]
                        self.drawColor = (0, 0, 0)
                    
                    elif 1150 < x1 < 1280:
                        self.header = overlayList[4]
                        self.imgCanvas = self.canvasClear
                        self.canvasClear = np.zeros((720, 1280, 3), np.uint8)
                        self.drawColor = (0,0,0)
                    
                cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), self.drawColor, cv2.FILLED)
            
            if fingers[1] and fingers[2] == False:
                cv2.circle(img, (x1, y1), 15, self.drawColor, cv2.FILLED)

                if self.drawColor == (0,0,0):
                    cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, self.eraserSize)
                    cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, self.eraserSize)

                if self.xp == 0 and self.yp == 0:
                    self.xp, self.yp = x1, y1
                
                else:
                    cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, self.brushThickness)
                    cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, self.brushThickness)
                
                self.xp, self.yp = x1, y1


            imgGray = cv2.cvtColor(self.imgCanvas, cv2.COLOR_BGR2GRAY)
            _, imgInverse = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
            imgInverse = cv2.cvtColor(imgInverse, cv2.COLOR_GRAY2BGR)
            img = cv2.bitwise_and(img, imgInverse)
            img = cv2.bitwise_or(img, self.imgCanvas)
            img[0:125, 0:1280] = self.header
            success, image = cv2.imencode('.jpg', img)
            return image.tobytes(), self.imgCanvas, img
            
        elif lmList == []:
            imgGray = cv2.cvtColor(self.imgCanvas, cv2.COLOR_BGR2GRAY)
            _, imgInverse = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
            imgInverse = cv2.cvtColor(imgInverse, cv2.COLOR_GRAY2BGR)
            img = cv2.bitwise_and(img, imgInverse)
            img = cv2.bitwise_or(img, self.imgCanvas)
            img[0:125, 0:1280] = self.header
            success, image = cv2.imencode('.jpg', img)
            return image.tobytes(), self.imgCanvas, img
            # return img , self.imgCanvas
        
        else:
            print("Errorrrrrr")
                    
def main():
    folderPath = "c://Users//HP//Desktop//Canvas flask app//app//static"
    myList = os.listdir(folderPath)
    overlayList = []
    for imgPath in myList:
        image = cv2.imread(f'{folderPath}/{imgPath}')
        overlayList.append(image)
    
    classes = image_class(overlayList)
    width = 1280
    height = 720
    cap = cv2.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)

    while True:
        success, img = cap.read()
        img = cv2.resize(img, (width, height))
        z, x, y = classes.generate_frame(img, overlayList)
        cv2.imshow("Image", x)
        cv2.imshow("Canvas", y)
        print(z)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    main()