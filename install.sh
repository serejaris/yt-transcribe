#!/usr/bin/env bash
# Installer for Video Transcriber

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="transcribe-video"

echo -e "${BLUE}🚀 Installing Video Transcriber...${NC}"
echo ""

# Create symlink
if [ -f "$INSTALL_DIR/$SCRIPT_NAME" ]; then
    echo -e "${YELLOW}⚠️  Removing existing installation...${NC}"
    sudo rm "$INSTALL_DIR/$SCRIPT_NAME"
fi

echo "Creating symlink..."
sudo ln -s "$SCRIPT_DIR/$SCRIPT_NAME" "$INSTALL_DIR/$SCRIPT_NAME"

# Make scripts executable
chmod +x "$SCRIPT_DIR/transcribe"
chmod +x "$SCRIPT_DIR/transcribe-video"
chmod +x "$SCRIPT_DIR/transcribe.py"

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "You can now use the transcriber from anywhere:"
echo ""
echo "  transcribe-video https://youtube.com/watch?v=..."
echo "  transcribe-video -m large https://youtube.com/watch?v=..."
echo "  transcribe-video --help"
echo ""
echo "To uninstall, run:"
echo "  sudo rm $INSTALL_DIR/$SCRIPT_NAME"
echo ""