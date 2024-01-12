#!/bin/bash

set -e
set -o pipefail

CONFIG_FILE="dionysus-config.ini"
COMPOSE_FILE="compose.yml"
ENV_FILE="${DIONYSUS_ENV_FILE:-.env}"

function log_error() {
  echo "Error: $1" >&2
}

function cleanup() {
  echo "Performing cleanup..."
  # Add cleanup logic here, if needed
}

function read_services_from_config() {
  # Read services from the INI file
  services=($(awk -F= '/^\[SERVICES\]/{flag=1;next}/^\[/{flag=0}flag{print $1}' "$CONFIG_FILE"))
  for service in "${services[@]}"; do
    if [ "$(awk -F= '/^\[SERVICES\]/{flag=1;next}/^\[/{flag=0}flag && /^'"$service"'=/{print $2}' "$CONFIG_FILE")" == "true" ]; then
      echo -f appdata/${service}/compose.override.yml
    fi
  done
}

function up_command() {
  echo "Starting Dionysus..."

  # Ensure compose.yml is included
  options=(-f $COMPOSE_FILE)

  # Add override files for services
  options+=($(read_services_from_config))

  # Specify the Docker Compose command with options, --env-file, and additional options
  echo "Usage: $0 up [options]"
  echo "Options:"
  echo "  Additional options for the underlying docker compose up command"
  echo ""
  echo "Example:"
  echo "  $0 up --build"
  echo "  $0 up -d"
  docker compose --env-file $ENV_FILE ${options[@]} up "$@"
}

function down_command() {
  echo "Tearing down Dionysus..."

  # Ensure compose.yml is included
  options=(-f $COMPOSE_FILE)

  # Add override files for services
  options+=($(read_services_from_config))

  # Specify the Docker Compose down command with options, --env-file, and additional options
  echo "Usage: $0 down [options]"
  echo "Options:"
  echo "  Additional options for the underlying docker compose down command"
  echo ""
  echo "Example:"
  echo "  $0 down -v"
  docker compose --env-file $ENV_FILE ${options[@]} down "$@"
}

function help_command() {
  echo "Usage: $0 <subcommand> [options]"
  echo "Subcommands:"
  echo "  up   - Start Dionysus services"
  echo "  down - Teardown Dionysus services"
  echo "  help - Show this help message"
  echo "Options:"
  echo "  Additional options for the underlying docker compose commands"
  echo ""
  echo "Examples:"
  echo "  $0 up --build"
  echo "  $0 down -v"
}

trap cleanup EXIT

case "$1" in
  up)
    shift # remove the subcommand
    up_command "$@"
    ;;
  down)
    shift # remove the subcommand
    down_command "$@"
    ;;
  help)
    help_command
    ;;
  *)
    log_error "Unknown subcommand: $1"
    help_command
    exit 1
    ;;
esac

echo "Dionysus script execution completed."