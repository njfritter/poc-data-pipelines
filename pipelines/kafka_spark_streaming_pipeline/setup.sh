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
        q) quickstart=true;;
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
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> /Users/fritteryerra/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "Updating Homebrew"
    brew update
fi

# Install kafka
brew install kafka

# Setup Kafka topics for our Coinbase data
kafka-topics --create --bootstrap-server '127.0.0.1:12345' --topic coinbase_trades
kafka-topics --create --bootstrap-server '127.0.0.1:12345' --topic coinbase_products

# Set up python3 virtual environment, activate it and install requirements
python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt 