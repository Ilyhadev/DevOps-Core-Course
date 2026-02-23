# Makefile for Lab1 (Docker build / measure targets)
.PHONY: all python-build-python-image python-run-python python-image-size \
        go-build-image go-run-go go-image-size compare-sizes clean

all: python-image-size go-image-size compare-sizes

# Python image targets
python-build-image:
	docker build -t devops-info-python:lab02 \
		-f app_python/Dockerfile app_python

python-run:
	docker run --rm -p 8080:8080 -e PORT=8080 devops-info-python:lab02

python-image-size:
	@echo "-- python image --"
	@docker images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep devops-info-python || true

# Go image targets
go-build-image:
	docker build -t devops-info-go:lab02 -f app_go/Dockerfile app_go

go-run:
	docker run --rm -p 8080:8080 devops-info-go:lab02

go-image-size:
	@echo "-- go image --"
	@docker images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep devops-info-go || true

# Compare both images
compare-sizes: python-image-size go-image-size

clean:
	rm -f app_python.tar.gz || true
	docker image rm devops-info-python:lab02 devops-info-go:lab02 || true
