PYTHON := ~/Library/Application\ Support/Autodesk/webdeploy/shared/PYTHON/3.5.3c/mac64_sp/Python.framework/Versions/3.5/bin/python

.PHONY: build run

build:
	rm -rf build/debug
	mkdir -p build/debug/plethora
	cd html && npm run build
	cp -r *.py build/debug/plethora/
	cp -r resources build/debug/plethora/
	cp Plethora.manifest build/debug/plethora/

run-web:
	cd html && npm run serve
