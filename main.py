import argparse
import datetime
import time
import ftplib
import fcntl
import os
import pathlib
import logging
import sys

import gphoto2 as gp
from gphoto2 import file


logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s - %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)

LOG_DIR = pathlib.Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
log = LOG_DIR / f"{datetime.datetime.now().strftime('%Y-%m-%d')}-photobooth.log"
filehandler = logging.FileHandler(log)
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)

PHOTO_DIR = pathlib.Path(__file__).parent / "pictures/raw"
PORT = 26000


def send(picture: pathlib.Path, ftp: ftplib.FTP):
    logger.info("Sending picture to FTP...")
    send_picture(picture, ftp)
    move_picture(picture)


def send_picture(picture: pathlib.Path, ftp: ftplib.FTP):
    with open(picture, "rb") as f:
        ftp.storbinary(f"STOR {picture.name}", f)


def move_picture(picture: pathlib.Path):
    sent = str(picture).replace("raw", "sent")
    picture.rename(sent)


def retry_loop(func):
    def inner(*args):
        timeout = time.time() + 60 * 15
        while True:
            try:
                if time.time() > timeout:
                    logger.warning("Retry exceeded")
                    sys.exit(1)
                result = func(*args)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt. Shutting down...")
                sys.exit(0)
            except:
                time.sleep(2)
                continue
            break
        return result

    return inner


@retry_loop
def connect_to_camera():
    camera = gp.Camera()
    camera.init()
    logger.info("Successfully connected to camera")
    return camera


@retry_loop
def connect(ip: str, port: int) -> ftplib.FTP:
    ftp = ftplib.FTP()
    ftp.connect(ip, port)
    logger.info("Successfully connected to FTP")
    return ftp


def read_ip(file: pathlib.Path = None):
    if not file:
        file = pathlib.Path.cwd() / "ip.json"
    with open(file, "r") as f:
        ip = f.read()
    return ip


def main(args: argparse.Namespace = None):
    logger.info("Connecting to camera...")
    camera = connect_to_camera()

    logger.info("Connecting to FTP...")
    ip = read_ip(args.ip_file or None)
    logger.info(f"IP: {args.ip or ip}, Port: {args.port or PORT}")
    ftp = connect(args.ip or ip, PORT)

    fl = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

    pathlib.Path(PHOTO_DIR).mkdir(exist_ok=True, parents=True)
    pathlib.Path(str(PHOTO_DIR).replace("raw", "sent")).mkdir(
        parents=True, exist_ok=True
    )
    timeout = 3000  # milliseconds
    logger.info("Waiting for event...")
    while True:
        try:
            event_type, event_data = camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL
                )
                picture = pathlib.Path(PHOTO_DIR) / event_data.name
                logger.info(f"Saving image to {picture}...")
                cam_file.save(str(picture))
                send(picture, ftp)
        except KeyboardInterrupt:
            ftp.close()
            camera.exit()
            sys.exit(0)
        except gp.GPhoto2Error:
            logger.warning("Camera disconnected. Retrying...")
            camera = connect_to_camera()
            logger.info("Waiting for event...")
            continue
    return 0


def cli():
    parser = argparse.ArgumentParser(
        prog="Shuttersnitch",
        description="Monitor for camera with Shuttersnitch integration",
    )

    parser.add_argument("--ip", dest="ip", help="IP-address of Shuttersnitch server")
    parser.add_argument("--port", dest="port", help="Port of Shuttersnitch server")
    parser.add_argument(
        "-o", "--output", dest="output", help="Output directory for saved images"
    )
    parser.add_argument("--ip-file", dest="ip_file")

    args = parser.parse_args()
    main(args)


if __name__ == "__main__":
    cli()
