import argparse
import datetime
import time
import ftplib
import pathlib
import logging
import shutil
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

SENT_DIR = pathlib.Path("/mnt/usb/photobooth/")
if not SENT_DIR.exists():
    SENT_DIR = pathlib.Path(str(PHOTO_DIR).replace("raw", "sent"))

PORT = 26000


def send(picture: pathlib.Path, ftp: ftplib.FTP):
    """Abstraction function to send picture and move it to
    archive.

    Args:
        picture (pathlib.Path): Path to picture saved from camera
        ftp (ftplib.FTP): FTP connection
    """
    logger.info("Sending picture to FTP...")
    send_picture(picture, ftp)
    move_picture(picture)


def send_picture(picture: pathlib.Path, ftp: ftplib.FTP):
    """Send picture via FTP.

    Args:
        picture (pathlib.Path): Path to picture saved from camera
        ftp (ftplib.FTP): FTP connection
    """
    with open(picture, "rb") as f:
        ftp.storbinary(f"STOR {picture.name}", f)


def move_picture(picture: pathlib.Path):
    """Move picture to archive.

    Args:
        picture (pathlib.Path): Path to picture saved from camera
    """
    logger.info("Moving picture to archive")
    sent = SENT_DIR / picture.name
    shutil.copyfile(picture, sent)


def retry_loop(func):
    """Decorator function to retry functions.
    Used to keep trying to connect to camera and FTP server.
    """
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
def connect_to_camera() -> gp.Camera:
    """Instantiate the Camera object.

    Returns:
        gp.Camera: Camera object from gphoto2
    """
    camera = gp.Camera()
    camera.init()
    logger.info("Successfully connected to camera")
    return camera


@retry_loop
def connect(ip: str, port: int) -> ftplib.FTP:
    """Connect to FTP server.

    Args: 
        ip (str): IP address of FTP server
        port (int): Port of FTP server

    Returns:
        ftplib.FTP: FTP object
    """
    ftp = ftplib.FTP()
    ftp.connect(ip, port)
    logger.info("Successfully connected to FTP")
    return ftp


def read_ip(file: pathlib.Path = None) -> str:
    """Read the IP address from file

    Args:
        file (pathlib.Path): Optional - Specify the file to read from

    Returns:
        str - IP address
    """
    if not file:
        file = pathlib.Path.cwd() / "ip.json"
    with open(file, "r") as f:
        ip = f.read().strip()
    return ip


def get_max_file(folder: pathlib.Path) -> str:
    """
    Get the number of files already in the sent folder and increment current file number.

    This is necessary if the camera connection is lost, which causes the first picture taken
    afterwards to be named "capt0000.jpg" again. Moving it would cause the previous picture
    to be overwritten.
    """
    try:
        max_file = max([int(file.stem[-4:]) for file in folder.rglob("*.jpg")])
        max_file = str(max_file + 1).zfill(4)
    except ValueError:
        max_file = "0000"
    file_name = f"capt{max_file}.jpg"
    return file_name


def main(args: argparse.Namespace = None):
    """Main logic of script.

    Process
    =======
    Script connects to camera and FTP server.
    Then it enters a loop, waiting for the event from the camera,
    i.e. the picture being taken.
    """
    logger.info("Connecting to camera...")
    camera = connect_to_camera()

    logger.info("Connecting to FTP...")
    ip = read_ip(args.ip_file or None)
    logger.info(f"IP: {args.ip or ip}, Port: {args.port or PORT}")
    ftp = connect(args.ip or ip, PORT)

    pathlib.Path(PHOTO_DIR).mkdir(exist_ok=True, parents=True)
    SENT_DIR.mkdir(exist_ok=True, parents=True)
    timeout = 3000  # milliseconds
    logger.info("Waiting for event...")
    while True:
        try:
            event_type, event_data = camera.wait_for_event(timeout)
            if event_type == gp.GP_EVENT_FILE_ADDED:
                cam_file = camera.file_get(
                    event_data.folder, event_data.name, gp.GP_FILE_TYPE_NORMAL
                )
                new_name = get_max_file(SENT_DIR)
                picture = pathlib.Path(PHOTO_DIR) / new_name
                logger.info(f"Saving image to {picture}...")
                cam_file.save(str(picture))
                send(picture, ftp)
                logger.info("Waiting for event...")
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
    """
    Main function to invoke script via CLI
    """
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
