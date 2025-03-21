# docker Pycharm Powershell 

# stopp all containers 
 docker ps -q | ForEach-Object { docker stop $_ }
 
# remove all containers 
docker ps -aq | ForEach-Object { docker rm $_ }

# remove all images 
docker rmi $(docker images -q)

## compined : 
docker ps -q | ForEach-Object { docker stop $_ }
docker ps -aq | ForEach-Object { docker rm $_ }
docker rmi $(docker images -q)

# prevent apt from asking questions during install 
ENV DEBIAN_FRONTEND=noninteractive

#  reduce the final image size.
`apt clean` → clears cached .deb files
`rm -rf /var/lib/apt/lists/* `→ removes downloaded package list metadata




