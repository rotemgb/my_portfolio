#!/bin/bash
virtual_env_name=rotemgb_env

source virtual_env/bin/activate
echo "Environment Activated"

python3 -m pip install --upgrade pip
python3 -m ipykernel install --user --name=$virtual_env_name --display-name=$virtual_env_name

echo "Kernel Installed"
