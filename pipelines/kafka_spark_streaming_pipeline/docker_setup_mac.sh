#!/bin/bash
# Setup script to download any required dependencies, set environment variables, etc.

set -e

Help ()
{
    # Display help + required arguments
    echo "Setup script for Real Time Coinbase Data pipeline"
    echo
    echo "Syntax: bash setup.sh [-h]"
    echo "options:"
    echo "h     Print this help."
}

# First prompt for required command line arguments (exit script if not used correctly)
while getopts "qh" flag; do
    case "${flag}" in
        h) 
           Help # Display help
           exit;;
        \?) 
            echo "Error: invalid option"
            exit;;
    esac
done

# Install homebrew (required) if it is not installed
# Explanation for using "command" over "which" to detect if a program is installed: https://stackoverflow.com/a/46998376
if [[ $(command -v brew) == "" ]]; then
    echo "Installing Homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
    echo "Adding homebrew to PATH" # https://stackoverflow.com/a/70006281
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $HOME/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "Updating Homebrew"
    brew update
fi

# Install Docker + Docker Compose (and make docker compose executable)
brew install docker && brew install docker-compose && sudo chmod +x /opt/homebrew/bin/docker-compose