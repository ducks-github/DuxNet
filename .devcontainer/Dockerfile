# DuxNet Dev Container Dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies for PyQt5 and GUI support
RUN apt-get update \
    && apt-get install -y libgl1-mesa-glx libxkbcommon-x11-0 \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# (Optional) Install any additional tools or dependencies here

# Set the default workdir
WORKDIR /workspaces/DuxNet
