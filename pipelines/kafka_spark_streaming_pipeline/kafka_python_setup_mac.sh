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

# Install kafka CLI tool to create Kafka topics for our Coinbase data
# TODO: See if this step can be replaced by accessing the Kafka container terminal
# Reference StackOverflow: https://stackoverflow.com/questions/30172605/how-do-i-get-into-a-docker-containers-shell
brew install kafka
kafka-topics --create --bootstrap-server '127.0.0.1:12345' --topic coinbase_trades_raw_data
kafka-topics --create --bootstrap-server '127.0.0.1:12345' --topic coinbase_trade_aggregated_metrics

# Set up python3 virtual environment, activate it and install requirements
python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt 