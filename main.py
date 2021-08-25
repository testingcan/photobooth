import argparse
import ftplib
import fcntl
import os
import pathlib
import logging
import sys

import gphoto2 as gp


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(levelname)s - %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)
PHOTO_DIR = pathlib.Path(__file__).parent / "pictures/raw"
IP = "192.168.178.44"
PORT = 26000


def connect(ip: str, port: int) -> ftplib.FTP:
    logger.info(f"IP: {ip}, Port: {port}")
    ftp = ftplib.FTP()
    ftp.connect(ip, port)
    return ftp


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


def main(args: argparse.Namespace = None):
    logger.info("Connecting to camera...")
    camera = gp.Camera()
    camera.init()

    logger.info("Connecting to FTP...")
    ftp = connect(args.ip or IP, PORT)

    fl = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

    pathlib.Path(PHOTO_DIR).mkdir(exist_ok=True, parents=True)
    pathlib.Path(str(PHOTO_DIR).replace("raw", "sent")).mkdir(
        parents=True, exist_ok=True
    )
    timeout = 3000  # milliseconds
    logger.info("Waiting for event...")
    try:
        while True:
            event_type, event_data = camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL
                )
                print(cam_file)
                picture = pathlib.Path(PHOTO_DIR) / event_data.name
                logger.info(f"Saving image to {picture}...")
                # print("Image is being saved to {}".format(picture))
                cam_file.save(str(picture))
                send(picture, ftp)
    except KeyboardInterrupt:
        ftp.close()
        camera.exit()
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

    args = parser.parse_args()
    main(args)


if __name__ == "__main__":
    cli()
