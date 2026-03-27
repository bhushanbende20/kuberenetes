#!/bin/sh
echo "Starting build..."
# First upgrade pip
pip install --upgrade pip setuptools wheel
# Then install requirements
pip install -r ${SRC_PKG}/requirements.txt -t ${SRC_PKG}
echo "Build complete!"