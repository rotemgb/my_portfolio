#!/bin/bash

virtual_env_name=rotemgb_env
python3 -m pip install --upgrade pip
python3 -m venv virtual_env

source virtual_env/bin/activate

pip install -r requirements.txt

echo "---------------------------"
echo "Installing Packages"
echo "---------------------------"

pip install ipykernel
python3 -m ipykernel install --user --name=$virtual_env_name
