# -*- coding: utf-8 -*-

import os


script_directory = os.path.dirname(os.path.realpath(__file__))
app_root = os.path.join(script_directory, os.pardir, os.pardir)
main_compose_file = os.path.join(app_root, "compose.yml")
config_file_path = os.path.join(app_root, "dionysus-config.ini")
service_directory_path = os.path.join(app_root, "appdata")

output_version_file = os.path.join(app_root, ".env.service_versions")

service_section = "SERVICES"
local_images = ["diofileserver"]
main_service = "heimdall"

github_personal_token_env_var = "GITHUB_PERSONAL_TOKEN"
github_personal_token = os.environ.get(github_personal_token_env_var)

dockerhub_personal_token_env_var = "DOCKERHUB_PERSONAL_TOKEN"
dockerhub_personal_token = os.environ.get(dockerhub_personal_token_env_var)
