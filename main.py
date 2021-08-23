from ftplib import FTP
import pathlib


def main():
    path = pathlib.Path.cwd() / "pictures"
    for picture in path.rglob("*.jpg"):
        send_picture(picture)


def send_picture(picture: pathlib.Path):
    ip = "192.168.178.44"
    port = 26000
    ftp = FTP()
    ftp.connect(ip, port)
    with open(picture, "rb") as f:
        ftp.storbinary(f"STOR {picture}", f)
    ftp.close()


if __name__ == "__main__":
    main()
