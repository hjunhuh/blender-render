#!/usr/bin/env bash
# Render the 4K turntable on a rented Linux NVIDIA GPU server (RTX 4090/5090 etc.)
# Usage on the server:  bash render_on_gpu_server.sh [blend_file] [start] [end]
set -euo pipefail

BLEND="${1:-aluminum_slab_4k.blend}"
START="${2:-1}"
END="${3:-240}"
BV="5.2.3"                                   # same version as the Mac that made the file
BDIR="blender-${BV}-linux-x64"

# 1) libraries Blender needs on a headless Ubuntu/Debian box
if command -v apt-get >/dev/null 2>&1; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO apt-get update -qq
  $SUDO apt-get install -y -qq libxrender1 libxi6 libxkbcommon0 libsm6 libxxf86vm1 libgl1 libegl1 xz-utils curl >/dev/null
fi

# 2) Blender
if [ ! -x "${BDIR}/blender" ]; then
  curl -L --fail -o blender.tar.xz "https://download.blender.org/release/Blender5.2/${BDIR}.tar.xz"
  tar -xf blender.tar.xz
fi

nvidia-smi --query-gpu=name,memory.total --format=csv

# 3) one test frame first: checks the GPU is used and measures time per frame
mkdir -p render/frames
T0=$(date +%s)
"${BDIR}/blender" -b "$BLEND" -o //render/test_4k_ -F PNG -f "$START" -- --cycles-device OPTIX
T1=$(date +%s)
PER=$((T1 - T0))
echo "Test frame took ${PER}s. Full range estimate: $(( PER * (END - START + 1) / 60 )) min"

# 4) full range (skips frames that already exist, so it can be re-run after a stop)
"${BDIR}/blender" -b "$BLEND" -s "$START" -e "$END" -a -- --cycles-device OPTIX

# 5) pack the frames for download
tar -cf frames_4k.tar -C render frames
echo "Done -> $(pwd)/frames_4k.tar"
