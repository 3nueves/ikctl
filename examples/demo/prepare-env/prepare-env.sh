#!/bin/bash
# prepare-env.sh
# Installs base packages and outputs environment info for subsequent kits.
set -e

echo "==> Updating package list..."
apt-get update -qq

echo "==> Installing base packages..."
apt-get install -y -qq curl wget jq

echo "==> Gathering environment info..."
DETECTED_HOSTNAME=$(hostname -s)
DETECTED_OS=$(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)

echo "==> Environment ready on: $DETECTED_HOSTNAME"

# Output variables for subsequent pipeline steps (KEY=VALUE format)
echo "HOSTNAME=$DETECTED_HOSTNAME"
echo "OS_VERSION=$DETECTED_OS"
echo "PACKAGES_OK=true"
