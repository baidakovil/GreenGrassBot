#!/bin/bash

containername="greengrassbot"
dockerhubrepo="baidakovil/greengrassbot:main"

# checks if container exist
if [ "$(docker ps --all --quiet --filter name=$containername)" ]
then
    echo "An existing container with the name $containername was found!"
    
    # checks if container is running and stop it if it is
    if [ "$(docker ps -aq -f status=running -f name=$containername)" ]
    then
        echo "Stopping container $containername..."
        docker stop $containername
	echo "Container stopped."
    fi

    # removes stopped container
    echo "Removing stopped container $containername..."
    docker rm $containername
    echo "Container $containername removed."
fi

# pull the latest image
docker pull $dockerhubrepo

# run new docker container. be sure to run this file from subdirectory of .env
docker run -d --name $containername --env-file ../.env --restart=always $dockerhubrepo
echo "Container $containername run."