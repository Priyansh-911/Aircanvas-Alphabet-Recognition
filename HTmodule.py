import cv2
import mediapipe as mp
import time


class handDetector():

    def __init__(self, mode=False, maxHands=2, complexity=1, detectionCon=0.5, trackCon=0.5):

        self.mode = mode
        self.maxHands = maxHands
        self.complexity = complexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.complexity, self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLMS in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLMS, self.mpHands.HAND_CONNECTIONS)

        return img

    def trackPos(self, img, handNo=0, draw=True):

        self.lmList = []
        if self.results.multi_hand_landmarks:
            handLMS = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(handLMS.landmark):
                # print(id,lm)
                h, w, c = img.shape
                hx, hy = int(lm.x * w), int(lm.y * h)
                # print(id, hx, hy)
                self.lmList.append([id, hx, hy])
                if draw:
                    cv2.circle(img, (hx, hy), 10, (150, 0, 150), cv2.FILLED)
        return self.lmList

    def fingerUp(self):
        fingers = []

        # for Thumb
        if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # for other fingers
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers


def main():
    pT = 0
    cT = 0
    cap = cv2.VideoCapture(0)
    detector = handDetector()

    while True:
        success, img = cap.read()
        img = detector.findHands(img)

        cT = time.time()
        fps = 1 / (cT - pT)
        pT = cT
        cv2.putText(img, str(int(fps)), (10, 100), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), )

        lmList = detector.trackPos(img, draw=False)

        if len(lmList) != 0:
            print(lmList)

        cv2.imshow("image", img)
        cv2.waitKey(1)


if __name__ == "__main__":
    main()
