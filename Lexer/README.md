******************************************
Installation of PLY and running the Lexer
******************************************


1) Download PLY from https://pypi.python.org/packages/source/p/ply/ply-3.8.tar.gz#md5=94726411496c52c87c2b9429b12d5c50

2) Unzip it (tar xvfz ply-3.8.tar.gz)

3) Install PLY with "python3 setup.py install" as root in the ply-3.8 folder

4) Use "python3 our_lexer.py <input_file>" to run the lexer for the <input_file>


OR

1) In a terminal, type "make install" to install PLY (same as steps 1-3 above)

2) Type "make", "make run" or "make tests" to run our Lexer with "lexer_test.txt" as default input file

3) Type "INPUT=<input_file> make run" to run our Lexer with <input_file>

