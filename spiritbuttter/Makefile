all: main feeds learn shawscript set usi

main:
	python do-skin.py

feeds:
	python feeds.py

learn:
	cd ../learn;make

shawscript:
	cd ../shawscript;make

usi:
	git update-server-info
	cd ../learn;git update-server-info

set:
	cd setmaker;make