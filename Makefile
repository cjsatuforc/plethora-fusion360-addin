PYTHON := ~/Library/Application\ Support/Autodesk/webdeploy/shared/PYTHON/3.5.3c/mac64_sp/Python.framework/Versions/3.5/bin/python

.PHONY: build run package

build:
	rm -rf palette
	cd html && npm run build

run-web:
	cd html && npm run serve

package: build
	rm -rf output
	mkdir -p output/plethora-fusion360-addin
	cp -R palette output/plethora-fusion360-addin
	cp -R resources output/plethora-fusion360-addin
	cp *.py output/plethora-fusion360-addin
	cp Plethora.manifest output/plethora-fusion360-addin
	cd output && zip -r -X plethora-fusion360-addin.zip plethora-fusion360-addin && rm -rf plethora-fusion360-addin