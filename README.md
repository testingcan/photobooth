# Photobooth

Build a simple photobooth using Python and [Shuttersnitch](https://www.shuttersnitch.com/).

## Description

This module is used to build a simple photobooth. The process is simple,
using only a small computer (e.g. a Raspberry Pi) with a camera connected
to it and a phone or tablet running Shuttersnitch. The process is then:

1. wait for event (i.e. picture taken) from camera
2. fetch the image from the camera and save it
3. send the picture to Shuttersnitch via FTP
4. (optional) archive the picture to a USB drive

## Requirements

The script requires [gphoto2](http://gphoto.org/) as well as a compatible camera.
Additionally it is strongly recommended to set up some sort of Hotspot on the device,
to which the Tablet or Phone can connect. The easiest way would be to set up [RaspAP](https://raspap.com/)
on a Raspberry Pi for this.

## Usage

You can:

* Start the script manually using `python main.py` (use `-h` for args)
* (recommended) Set up the script as a Service to run it in the background

The only thing you need to set is the IP address. Either specify it via `--ip` or set it directly
in the file `ip.json`.
