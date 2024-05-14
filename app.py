from flask import Flask, render_template, Response
import cv2
import numpy as np
import os
import HTmodule as htm
# import time
# import Camera as camera

import test as T

# cam = cv2.VideoCapture(0)
app = Flask(__name__)

# cameras = camera()
# print(vars(camera).keys())
# print(cameras.cam)
# print(cameras.video)
# print(camera.__init__())


def generate():
    folderPath = "static"
    myList = os.listdir(folderPath)
    overlayList = []
    for imgPath in myList:
        image = cv2.imread(f'{folderPath}/{imgPath}')
        overlayList.append(image)
    width = 1280
    height = 720
    classes = T.image_class(overlayList)
    cap = cv2.VideoCapture(0)
    cap.set(3, width)
    cap.set(4, height)
    while True:
        suc, img = cap.read()
        # img = cv2.resize(img, (width, height))
        x,y,z = classes.generate_frame(img, overlayList)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + x + b'\r\n\r\n')
        # cv2.imshow("Image", y)
        # cv2.imshow("Canvas", z)
                     
                    

# def canvas():
#       while True:
#             frame = Camera.canvas_frames()
#             yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

            

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/canvas_feed')
# def canvas_feed():
#       return Response(canvas(), mimetype='multipart/x-mixed-replace; boundary=frame')

# if __name__ == "__main__":
#     app.run(debug=True)