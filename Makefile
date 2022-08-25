clean:
	rm -f build/*

build: clean
	go build -o build/ ./...

run: build
	./build/cmd