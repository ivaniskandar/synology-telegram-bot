.PHONY: build

newtag ?= latest

image = ivaniskandar/syno-tele

build:
	docker build --no-cache=true -t "${image}:latest" .
	docker tag "${image}:latest" "${image}:${newtag}"

buildtest:
	docker build -t "${image}:testing" .

buildtestimage:
	docker build -t "${image}:testing" .
	docker save "${image}:testing" | gzip > testing.tar.gz

push:
	docker push ${image}:${newtag}
	docker push ${image}:latest

clean:
	-docker kill $(docker ps -q)
	-docker rm $(docker ps -a -q)
	-docker rmi $(docker images -a --filter=dangling=true -q)
