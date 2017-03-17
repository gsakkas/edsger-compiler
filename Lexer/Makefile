INPUT ?= ./lexer_test.txt

# Typing "make" without arguments runs the Lexer with the default input
also_run: tests

# Install the PLY library
install: unzip clean
	cd ./ply-3.8; sudo python3 setup.py install

# Unzip the downloaded file
unzip: download
	tar xvfz ply-3.8.tar.gz

# Download the compressed PLY library
download:
	wget https://pypi.python.org/packages/source/p/ply/ply-3.8.tar.gz#md5=94726411496c52c87c2b9429b12d5c50

# Run our Lexer with INPUT as the input file
# Usage: INPUT=<input_file> make run
# 	By default "make run" will run
#	with "lexer_test.txt", same as "make tests"
run:
	python3 our_lexer.py ${INPUT}

tests:
	python3 our_lexer.py lexer_test.txt

clean:
	rm ply-3.8.tar.gz
