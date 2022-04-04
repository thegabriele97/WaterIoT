.PHONY: genreq

genreq: requirements.txt
	@./gen.sh

requirements.txt: *.py
	@pipreqs --force
