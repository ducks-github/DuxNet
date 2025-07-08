#!/bin/bash
# Run the DuxNet desktop GUI in Docker with X11 forwarding

IMAGE_NAME=duxnet-gui

# Build the image (if not already built)
docker build -f Dockerfile.gui -t $IMAGE_NAME .

# Detect host OS and set DISPLAY/X11 options
echo "DISPLAY is $DISPLAY"

# For Linux hosts (native X11)
docker run --rm -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    $IMAGE_NAME

# For Windows with VcXsrv/Xming, you may need to allow connections:
#   xhost +local:docker
# And set DISPLAY=host.docker.internal:0 or your Windows IP 