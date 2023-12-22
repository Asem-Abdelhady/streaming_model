import argparse
import asyncio
import json
import os
import ssl
import uuid
import time

from aiohttp import web
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
import aiohttp_cors
from av import VideoFrame
from object_detection import ObjectDetector
from face_detection_mediapipe import FaceDetection

ROOT = os.path.dirname(__file__)

pcs = set()
relay = MediaRelay()
displayed_objects = dict()
to_display_objects = dict()
desired_objects = []


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track
        self.od = ObjectDetector()
        self.fd = FaceDetection()

    async def recv(self):
        frame = await self.track.recv()

        img = frame.to_ndarray(format="bgr24")
        detected_frame, objects = self.od.detect(img)
        detected_frame = self.fd.detect(detected_frame)
        new_frame = VideoFrame.from_ndarray(detected_frame, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        for object in objects:
            if object not in displayed_objects and object not in to_display_objects:
                to_display_objects[object] = time.gmtime()
        return new_frame


async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    params = await request.json()
    print("Offer is ", params)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        print("Data channel")
        @channel.on("message")
        def on_message(message):
            desired_objects = message.split("|")
            for key in to_display_objects:
                if key not in displayed_objects and key in desired_objects:
                    channel.send(
                        f'{key} : {time.strftime("%a, %d %b %Y %H:%M:%S +0000", to_display_objects[key])}')
                    displayed_objects[key] = to_display_objects[key]

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection stage: ")
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        print("track")
        if track.kind == "video":
            pc.addTrack(
                VideoTransformTrack(
                    relay.subscribe(track)
                )
            )

    # handle offer
    await pc.setRemoteDescription(offer)

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        )
    print("text: ", text)
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    print("Shutting down")
    pcs.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC audio / video / data-channels demo"
    )
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    args = parser.parse_args()

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

    web.run_app(
        app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context
    )
