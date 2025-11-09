#!/bin/bash
# Setup script for Railway deployment
# Installs ffmpeg for audio conversion

echo "Installing ffmpeg for audio conversion..."

# Check if we're on a Debian/Ubuntu-based system (Railway typically uses Ubuntu)
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y ffmpeg
    echo "ffmpeg installed successfully"
elif command -v yum &> /dev/null; then
    # For CentOS/RHEL-based systems
    yum install -y ffmpeg
    echo "ffmpeg installed successfully"
elif command -v brew &> /dev/null; then
    # For macOS (local development)
    brew install ffmpeg
    echo "ffmpeg installed successfully"
else
    echo "Warning: Could not detect package manager. ffmpeg may not be installed."
    echo "Please ensure ffmpeg is available for audio conversion to work."
fi

# Verify ffmpeg installation
if command -v ffmpeg &> /dev/null; then
    ffmpeg -version
    echo "✓ ffmpeg is available"
else
    echo "✗ ffmpeg is not available"
fi

