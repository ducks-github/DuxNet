FROM debian:bookworm

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
    live-build \
    debootstrap \
    squashfs-tools \
    xorriso \
    grub-pc-bin \
    grub-efi-amd64-bin \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy theme customizations
COPY config/ ./config/

# Copy build script
COPY build_duxos_simple.sh ./

# Make the script executable
RUN chmod +x build_duxos_simple.sh

# Set the default command
CMD ["./build_duxos_simple.sh"] 