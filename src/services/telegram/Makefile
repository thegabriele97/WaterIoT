.PHONY: genreq

genreq: requirements.txt

requirements.txt: *.py
	@pipreqs --force
	sed -i 's/python_bcrypt==0.3.2/bcrypt==3.2.0/g' requirements.txt
