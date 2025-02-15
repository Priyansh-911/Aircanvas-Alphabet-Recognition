import os
import asyncio
import threading
import json
import cv2
import logging
from flask import Flask, render_template, send_from_directory
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder
import numpy as np
from av import VideoFrame
import websockets
import test as T

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video-app")

# Flask app setup
app = Flask(__name__)
pcs = set()

# Load overlay images
folderPath = "static"
try:
    overlayList = [cv2.imread(f"{folderPath}/{imgPath}") for imgPath in os.listdir(folderPath)]
    classes = T.image_class(overlayList)
    logger.info(f"Loaded {len(overlayList)} overlay images from {folderPath}")
except Exception as e:
    logger.error(f"Error loading overlay images: {e}")
    overlayList = []
    classes = None

# Video processing track
class VideoTransformTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        
        # Get the frame as numpy array
        img = frame.to_ndarray(format="bgr24")
        img = cv2.resize(img, (1280, 720))
        
        # Process the frame using the test.py functionality
        if classes is not None:
            try:
                _, _, processed_img = classes.generate_frame(img, overlayList)
            except Exception as e:
                logger.error(f"Error in frame processing: {e}")
                processed_img = img
        else:
            processed_img = img
            
        # Reconstruct a VideoFrame from the processed ndarray
        processed_img = np.array(processed_img, dtype=np.uint8)
        new_frame = VideoFrame.from_ndarray(processed_img, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        
        return new_frame

# WebRTC signaling - FIXED VERSION
# async def handle_websocket(websocket, path=None):
#     logger.info("New WebSocket connection")
    
#     pc = RTCPeerConnection()
#     pcs.add(pc)
    
#     @pc.on("iceconnectionstatechange")
#     async def on_iceconnectionstatechange():
#         logger.info(f"ICE connection state is {pc.iceConnectionState}")
#         if pc.iceConnectionState == "failed":
#             await pc.close()
#             pcs.discard(pc)
    
#     @pc.on("track")
#     def on_track(track):
#         logger.info(f"Track {track.kind} received")
#         if track.kind == "video":
#             local_video = VideoTransformTrack(track)
#             pc.addTrack(local_video)
    
#     try:
#         async for message in websocket:
#             data = json.loads(message)
            
#             if data["type"] == "offer":
#                 logger.info("Received offer")
#                 offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
#                 await pc.setRemoteDescription(offer)
                
#                 answer = await pc.createAnswer()
#                 await pc.setLocalDescription(answer)
                
#                 response = {
#                     "type": "answer",
#                     "sdp": pc.localDescription.sdp,
#                 }
#                 await websocket.send(json.dumps(response))
                
#             elif data["type"] == "ice":
#                 logger.info("Received ICE candidate")
#                 if data["candidate"]:
#                     candidate = data["candidate"]
#                     await pc.addIceCandidate(candidate)
                    
#     except Exception as e:
#         logger.error(f"Error in websocket handling: {e}")
    
#     finally:
#         logger.info("WebSocket connection closed")
#         await pc.close()
#         pcs.discard(pc)

async def handle_websocket(websocket, path=None):
    logger.info("New WebSocket connection")
    
    pc = RTCPeerConnection()
    pcs.add(pc)
    
    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        logger.info(f"ICE connection state is {pc.iceConnectionState}")
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)
    
    @pc.on("track")
    def on_track(track):
        logger.info(f"Track {track.kind} received")
        if track.kind == "video":
            local_video = VideoTransformTrack(track)
            pc.addTrack(local_video)
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "offer":
                logger.info("Received offer")
                offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
                await pc.setRemoteDescription(offer)
                
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)
                
                response = {
                    "type": "answer",
                    "sdp": pc.localDescription.sdp,
                }
                await websocket.send(json.dumps(response))
                
            elif data["type"] == "ice":
                logger.info("Received ICE candidate")
                if data["candidate"]:
                    # Import RTCIceCandidate
                    from aiortc import RTCIceCandidate
                    
                    # Create proper RTCIceCandidate object
                    candidate_dict = data["candidate"]
                    
                    # Check if the required fields exist
                    if all(k in candidate_dict for k in ["candidate", "sdpMid", "sdpMLineIndex"]):
                        ice_candidate = RTCIceCandidate(
                            component=candidate_dict.get("component", 0),
                            foundation=candidate_dict.get("foundation", ""),
                            ip=candidate_dict.get("ip", ""),
                            port=candidate_dict.get("port", 0),
                            priority=candidate_dict.get("priority", 0),
                            protocol=candidate_dict.get("protocol", ""),
                            type=candidate_dict.get("type", ""),
                            sdpMid=candidate_dict["sdpMid"],
                            sdpMLineIndex=candidate_dict["sdpMLineIndex"],
                        )
                        await pc.addIceCandidate(ice_candidate)
                    else:
                        logger.warning(f"Incomplete ICE candidate received: {candidate_dict}")
                    
    except Exception as e:
        logger.error(f"Error in websocket handling: {e}")
    
    finally:
        logger.info("WebSocket connection closed")
        await pc.close()
        pcs.discard(pc)

# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

# Start WebSocket server - FIXED VERSION
async def start_websocket_server():
    logger.info("Starting WebSocket server on ws://localhost:8765")
    try:
        async with websockets.serve(handle_websocket, "0.0.0.0", 8765):
            await asyncio.Future()  # Keep the server running forever
    except TypeError:
        # Fallback for older websockets versions
        server = await websockets.serve(
            lambda ws, path: handle_websocket(ws, path), 
            "0.0.0.0", 
            8765
        )
        await asyncio.Future()  # Keep the server running forever

def run_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_server())

if __name__ == "__main__":
    # Start WebSocket server in a separate thread
    threading.Thread(target=run_websocket_server, daemon=True).start()
    
    # Start Flask server
    logger.info("Starting Flask server on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)