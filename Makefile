all: build run

build:
	docker build -t ibmosquito/aqi-orb:1.0.0 -f Dockerfile .

dev: build stop
	-docker rm -f aqi-orb 2> /dev/null || :
	docker run -it --privileged --name aqi-orb --volume `pwd`:/outside ibmosquito/aqi-orb:1.0.0 /bin/bash

run: stop
	-docker rm -f aqi-orb 2>/dev/null || :
	docker run -d --restart=unless-stopped --privileged --name aqi-orb ibmosquito/aqi-orb:1.0.0

exec:
	docker exec -it aqi-orb /bin/sh

push:
	docker push ibmosquito/aqi-orb:1.0.0

stop:
	-docker rm -f aqi-orb 2>/dev/null || :

clean: stop
	-docker rmi ibmosquito/aqi-orb:1.0.0 2>/dev/null || :

.PHONY: all build dev run exec push stop clean
