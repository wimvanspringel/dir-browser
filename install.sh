#!/bin/bash
set -x

# cp config.ini ~/nasdocker/dir-browser/config.ini
cp directory_server.py ~/nasdocker/dir-browser/directory_server.py
cp directory_client.html ~/nasdocker/dir-browser/directory_client.html
cp requirements.txt ~/nasdocker/dir-browser/requirements.txt
cp nginx.conf ~/nasdocker/dir-browser/nginx.conf
cp .dockerignore ~/nasdocker/dir-browser/.dockerignore
cp .gitignore ~/nasdocker/dir-browser/.gitignore
cp Dockerfile ~/nasdocker/dir-browser/Dockerfile
cp docker-compose.yml ~/nasdocker/dir-browser/docker-compose.yml
cp README-Docker.md ~/nasdocker/dir-browser/README-Docker.md
cp start_directory_server.sh ~/nasdocker/dir-browser/start_directory_server.sh
