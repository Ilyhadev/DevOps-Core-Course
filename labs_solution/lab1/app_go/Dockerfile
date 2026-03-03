# Multi-stage Dockerfile for Go (builder -> minimal runtime)
FROM golang:1.22 AS builder
WORKDIR /src

# cache modules
COPY go.mod ./
# If go.sum exists it will be used; otherwise `go mod download` will populate it from the network.
RUN go mod download

# copy and build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags="-s -w" -o /out/devops-info-service .

# final image: minimal runtime
FROM alpine:3.18
RUN addgroup -S app && adduser -S -G app -u 1000 app
COPY --from=builder /out/devops-info-service /usr/local/bin/devops-info-service
USER app
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/devops-info-service"]
