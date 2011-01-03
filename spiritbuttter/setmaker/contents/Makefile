all: shavian-set.sqlite

shavian-set.sqlite: shavian-set.xml
	python create-sqlite.py
	@echo Now run:  make test

test: shavian-set.sqlite demo-input.txt expected.txt
	@echo Comparing demo test to expected result:
	python read-back.py | diff -s - expected.txt

clean:
	rm -f shavian-set.sqlite
