# Photobooth

Build a simple photobooth using Python and [Shuttersnitch](https://www.shuttersnitch.com/).

## Description

This module is used to build a simple photobooth. The process is simple,
using only a small computer (e.g. a Raspberry Pi) with a camera connected
to it and a phone or tablet running Shuttersnitch. The process is then:

1. The script constantly waits for the camera to take a picture
2. Once it registers a picture being taken, it fetches the picture and saves 
it to the drive
3. The script then sends the picture via FTP to Shuttersnitch
4. (optional) The script then archives the picture to a USB drive

## Requirements

The script requires [gphoto2](http://gphoto.org/) as well as a compatible camera.
Additionally it is strongly recommended to set up some sort of Hotspot on the device,
to which the Tablet or Phone can connect. The easiest way would be to set up [RaspAP](https://raspap.com/)
on a Raspberry Pi for this.

