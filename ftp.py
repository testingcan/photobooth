import ftplib
import pathlib

PHOTO_DIR = pathlib.Path(__file__).parent / "pictures/raw"


def main():
    ip = "192.168.178.44"
    port = 26000
    ftp = connect(ip, port)
    for picture in PHOTO_DIR.rglob("*.JPG"):
        send_picture(picture, ftp)
        move_picture(picture)

    ftp.close()


def send_picture(picture: pathlib.Path, ftp: ftplib.FTP):
    with open(picture, "rb") as f:
        ftp.storbinary(f"STOR {picture.name}", f)


def move_picture(picture: pathlib.Path):
    sent = str(picture).replace("raw", "sent")
    picture.rename(sent)


def connect(ip: str, port: int) -> ftplib.FTP:
    ftp = ftplib.FTP()
    ftp.connect(ip, port)
    return ftp


if __name__ == "__main__":
    main()
