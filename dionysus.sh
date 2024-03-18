#!/bin/bash

set -e
set -o pipefail

CONFIG_FILE="dionysus-config.ini"
COMPOSE_FILE="compose.yml"
ENV_FILE="${DIONYSUS_ENV_FILE:-.env}"
SERVICE_VERSIONS_ENV_FILE=".env.service_versions"
APP_DIRECTORY="app"

function log_error() {
  echo "Error: $1" >&2
}

function cleanup() {
  echo "Performing cleanup..."
  
  # Prune images associated with services defined in CONFIG_FILE
  services=$(awk -F= '/^\[SERVICES\]/{flag=1;next}/^\[/{flag=0}flag{print $1}' "$CONFIG_FILE" | tr '\n' ' ')
  docker image prune -f --filter "label=com.docker.compose.project=dionysus $services"
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

function run_dioserviceupdater() {
  # Parse the environment file to extract the required variables
  if [ -f "$ENV_FILE" ]; then
    # Store the current directory
    previous_dir=$(pwd)

    GITHUB_PERSONAL_TOKEN=$(grep -E '^GITHUB_PERSONAL_TOKEN=' "$ENV_FILE" | cut -d '=' -f 2)
    DOCKERHUB_PERSONAL_TOKEN=$(grep -E '^DOCKERHUB_PERSONAL_TOKEN=' "$ENV_FILE" | cut -d '=' -f 2)

    # Change directory to app
    cd "$APP_DIRECTORY" || exit

    # Launch the dioserviceupdater with the given args and environment variables
    GITHUB_PERSONAL_TOKEN="$GITHUB_PERSONAL_TOKEN" DOCKERHUB_PERSONAL_TOKEN="$DOCKERHUB_PERSONAL_TOKEN" python3 -m dioserviceupdater "$@"

    # Restore the previous directory
    cd "$previous_dir" || exit

  else
    echo "Error: Environment file $ENV_FILE not found."
  fi
}

function up_command() {
  echo "Starting Dionysus..."

  # Ensure the environment file exists
  if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found."
    exit 1
  fi

  # Ensure .env.service_versions file exists
  if [ ! -f "$SERVICE_VERSIONS_ENV_FILE" ]; then
    echo "Error: Environment file $SERVICE_VERSIONS_ENV_FILE not found."
    exit 1
  fi

  # Ensure compose.yml is included
  options=(-f $COMPOSE_FILE)

  # Add override files for services
  options+=($(read_services_from_config))

  # Specify the Docker Compose command with options, --env-file, and additional options
  docker compose --env-file "$ENV_FILE" --env-file "$SERVICE_VERSIONS_ENV_FILE" ${options[@]} up "$@"
}

function down_command() {
  echo "Tearing down Dionysus..."

  # Ensure the environment file exists
  if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file $ENV_FILE not found."
    exit 1
  fi

  # Ensure .env.service_versions file exists
  if [ ! -f "$SERVICE_VERSIONS_ENV_FILE" ]; then
    echo "Error: Environment file $SERVICE_VERSIONS_ENV_FILE not found."
    exit 1
  fi

  # Ensure compose.yml is included
  options=(-f $COMPOSE_FILE)

  # Add override files for services
  options+=($(read_services_from_config))

  # Specify the Docker Compose down command with options, --env-file, and additional options
  docker compose --env-file "$ENV_FILE" --env-file "$SERVICE_VERSIONS_ENV_FILE" ${options[@]} down "$@"
}

function update_command() {
  echo "Updating Dionysus images..."

  # Run the dioserviceupdater
  run_dioserviceupdater "$@"
}

function configure_command() {
  echo "Configuring Dionysus..."
  
  if [ ! -f "$(dirname "$0")/.env.service_versions" ]; then
    # Run the dioserviceupdater
    run_dioserviceupdater "$@"
  else
    echo "Skipping configuration. The file .env.service_versions already exists."
  fi
}

function help_command() {
  echo "Usage: $0 <subcommand> [options]"
  echo "Subcommands:"
  echo "  up        - Start Dionysus services"
  echo "  down      - Teardown Dionysus services"
  echo "  update    - Update Dionysus images"
  echo "  configure - Configure Dionysus"
  echo "  help      - Show this help message"
  echo "Options:"
  echo "  Additional options for the underlying commands"
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
  update)
    shift # remove the subcommand
    update_command "$@"
    ;;
  configure)
    shift # remove the subcommand
    configure_command "$@"
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