#!/bin/bash

# Discord Music Bot Setup Script
# This script automates the initial setup process

echo "==================================="
echo "Discord Music Bot Setup Script"
echo "==================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_status() {
    if [ "$2" = "success" ]; then
        echo -e "\033[0;32m✓\033[0m $1"
    elif [ "$2" = "error" ]; then
        echo -e "\033[0;31m✗\033[0m $1"
    else
        echo -e "\033[0;33m→\033[0m $1"
    fi
}

# Check Python installation
print_status "Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python $PYTHON_VERSION found" "success"
else
    print_status "Python 3 not found. Please install Python 3.8 or higher" "error"
    exit 1
fi

# Check FFmpeg installation
print_status "Checking FFmpeg installation..."
if command_exists ffmpeg; then
    print_status "FFmpeg found" "success"
else
    print_status "FFmpeg not found" "error"
    echo ""
    echo "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ -d "venv" ]; then
    print_status "Virtual environment already exists" "success"
else
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        print_status "Virtual environment created" "success"
    else
        print_status "Failed to create virtual environment" "error"
        exit 1
    fi
fi

# Activate virtual environment
print_status "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_status "Virtual environment activated" "success"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    print_status "Virtual environment activated (Windows)" "success"
else
    print_status "Could not find activation script" "error"
    exit 1
fi

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip >/dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "Pip upgraded" "success"
else
    print_status "Failed to upgrade pip" "error"
fi

# Install requirements
print_status "Installing Python requirements..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    print_status "Requirements installed successfully" "success"
else
    print_status "Failed to install requirements" "error"
    exit 1
fi

# Setup environment file
print_status "Setting up environment configuration..."
if [ -f ".env" ]; then
    print_status ".env file already exists" "success"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status ".env file created from example" "success"
        echo ""
        echo "IMPORTANT: Edit .env file and add your Discord bot token"
        echo ""
    else
        print_status ".env.example not found" "error"
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p downloads
print_status "Directories created" "success"

# Final instructions
echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Discord bot token"
echo "2. Run the bot with: python main.py"
echo ""
echo "For development, activate the virtual environment with:"
echo "  source venv/bin/activate  # On Linux/macOS"
echo "  venv\\Scripts\\activate   # On Windows"
echo ""
print_status "Happy coding! 🎵" "success"