#!/bin/bash
# Setup script for Docker, Python packages, Postgres and more

set -e

Help ()
{
    # Display help + required arguments
    echo "Setup script for Docker, Python packages, Postgres and more"
    echo
    echo "Syntax: bash docker_setup_mac.sh [-h]"
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

# Set up python3 virtual environment, activate it and install requirements
python3 -m venv venv && source venv/bin/activate && pip3 install -r requirements.txt

# Install and start Postgres
# TODO: See if postgres should be explicitly uninstalled first
brew install postgres && brew services start postgresql

# Create new Postgres DB to store our Coinbase data
# NOTE: Versions 14.1+ of Postgres installed with Homebrew do NOT have a super user name `postgres` created by default
# https://stackoverflow.com/a/70491266
# Instead, there is a super user created whose name is based on the Mac's personal Home directory name
DEFAULT_POSTGRES_USER=$(id -u -n)
echo "Default Postgres user is: ${DEFAULT_POSTGRES_USER}"
# Below is equivalent to "create database if not exists" (https://stackoverflow.com/a/36591842)
psql -d postgres -U ${DEFAULT_POSTGRES_USER} -tc "SELECT 1 FROM pg_database WHERE datname = 'poc_data_pipelines'" | grep -q 1 || psql -d postgres -U ${DEFAULT_POSTGRES_USER} -c "CREATE DATABASE poc_data_pipelines"
sudo -u ${DEFAULT_POSTGRES_USER} psql -d poc_data_pipelines -c 'create schema if not exists kafka_spark_streaming_pipeline;'
sudo -u ${DEFAULT_POSTGRES_USER} psql -d poc_data_pipelines -c 'create table if not exists kafka_spark_streaming_pipeline.streaming_layer ( api_call_timestamp TIMESTAMP WITH TIME ZONE, product_id VARCHAR(15), num_trades INTEGER, num_sell_trades INTEGER, num_buy_trades INTEGER, share_volume REAL, avg_share_price REAL );'

# TODO: See if we can download Postgresql Spark jar here?
#wget https://jdbc.postgresql.org/download/postgresql-42.7.2.jar
#chmod +x postgresql-42.7.2.jar

# TODO: Implement Custom configurations referenced here for better performance: https://sqlpad.io/tutorial/postgres-mac-installation/
# Will attempt to change default configurations using this method:
# https://dba.stackexchange.com/questions/220700/how-to-edit-postgresql-conf-with-pgadmin-4

# TODO: Add custom user that will interact with the Postgres DB instead of the default user
# Use interactive prompt to create password via: https://dba.stackexchange.com/q/302682
# Apparently, creating a new user also requires editing the .conf file and choosing a specific authentication method over the default "peer" authentication method
# https://stackoverflow.com/a/66772164