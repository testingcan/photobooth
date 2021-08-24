import ftplib
import os
import pathlib

import gphoto2 as gp


PHOTO_DIR = pathlib.Path(__file__).parent / "pictures/raw"
IP = "192.168.178.44"
PORT = 26000


def connect(ip: str, port: int) -> ftplib.FTP:
    ftp = ftplib.FTP()
    ftp.connect(ip, port)
    return ftp


def send(picture: pathlib.Path, ftp: ftplib.FTP):
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
    camera = gp.Camera()
    camera.init()
    ftp = connect(IP, PORT)
    timeout = 3000  # milliseconds
    while True:
        event_type, event_data = camera.wait_for_event(timeout)
        if event_type == gp.GP_EVENT_FILE_ADDED:
            cam_file = camera.file_get(
                event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL
            )
            # target_path = os.path.join(PHOTO_DIR, event_data.name)
            picture = pathlib.Path(PHOTO_DIR) / event_data.name
            # print("Image is being saved to {}".format(picture))
            print(picture)
            cam_file.save(str(picture))
            send(picture, ftp)
    ftp.close()
    return 0


if __name__ == "__main__":
    main()
