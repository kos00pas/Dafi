# docker Pycharm Powershell 

# stopp all containers 
 docker ps -q | ForEach-Object { docker stop $_ }
 
# remove all containers 
docker ps -aq | ForEach-Object { docker rm $_ }

# remove all images 
docker rmi $(docker images -q)


#  Remove all containers except 2e996bde5e74:
docker ps -a -q | Where-Object { $_ -ne "2e996bde5e74" } | ForEach-Object { docker rm $_ }

#  Remove all images except f3f9d20d1278:

docker images -q | Where-Object { $_ -ne "f3f9d20d1278" } | ForEach-Object { docker rmi $_ }



## Clear everything : 
docker ps -q | ForEach-Object { docker stop $_ }
docker ps -aq | ForEach-Object { docker rm $_ }
docker rmi $(docker images -q)

# prevent apt from asking questions during install 
ENV DEBIAN_FRONTEND=noninteractive

#  reduce the final image size.
`apt clean` → clears cached .deb files
`rm -rf /var/lib/apt/lists/* `→ removes downloaded package list metadata


