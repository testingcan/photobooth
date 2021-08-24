import ftplib
import os
import pathlib
import logging

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


def main():
    # Init camera
    logger.info("Connecting to camera...")
    camera = gp.Camera()
    camera.init()
    logger.info("Connecting to FTP...")
    ftp = connect(IP, PORT)
    timeout = 3000  # milliseconds
    logger.info("Waiting for event...")
    while True:
        event_type, event_data = camera.wait_for_event(timeout)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            cam_file = camera.file_get(
                event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL
            )
            picture = pathlib.Path(PHOTO_DIR) / event_data.name
            logger.info(f"Saving image to {picture}...")
            # print("Image is being saved to {}".format(picture))
            cam_file.save(str(picture))
            send(picture, ftp)
    ftp.close()
    return 0


if __name__ == "__main__":
    main()
