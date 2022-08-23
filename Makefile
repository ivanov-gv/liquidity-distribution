APP_NAME=app

clean:
	rm -f build/${APP_NAME}

build: clean
	go build -o build/${APP_NAME} ./cmd

run: build
	PORT=${PORT} ./${APP_NAME}