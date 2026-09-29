#!/bin/bash
# Fast Python 3.14 setup for Ubuntu

export DEBIAN_FRONTEND=noninteractive

echo "Setting up Python 3.14..."

# Install Python 3.14 from deadsnakes (30 seconds, no compilation)
apt-get update -qq
apt-get install -y -qq software-properties-common curl
add-apt-repository -y ppa:deadsnakes/ppa > /dev/null 2>&1
apt-get update -qq
apt-get install -y -qq python3.14 python3.14-venv

# Setup virtual environment
cd /workspace
python3.14 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q requests urllib3 elasticsearch

echo "✅ Done! Run: source /workspace/venv/bin/activate"