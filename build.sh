#!/bin/sh
echo "Starting build process..."
echo "SRC_PKG = ${SRC_PKG}"
echo "DEPLOY_PKG = ${DEPLOY_PKG}"

# Make sure directories exist
mkdir -p ${DEPLOY_PKG}

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install dependencies directly into DEPLOY_PKG
pip install -r ${SRC_PKG}/requirements.txt -t ${DEPLOY_PKG}

# Copy function code to DEPLOY_PKG
cp ${SRC_PKG}/function.py ${DEPLOY_PKG}/

# List contents for debugging
echo "Contents of DEPLOY_PKG:"
ls -la ${DEPLOY_PKG}

echo "Build complete!"