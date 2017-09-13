# Makefile for installing the Edsger Compiler
.PHONY: all clean distclean

# Install the compiler (should be  superuser for this, e.g. "sudo -H make")
all: install_llvmlite make_libs install_numpy install_ply make_comp check_install

# Install llvmlite
install_llvmlite: install_pip install_pre
	apt-get install llvm-3.8
	apt-get install clang-3.8	
	LLVM_CONFIG=/usr/bin/llvm-config-3.8 pip install llvmlite

# Install python-pip
install_pip:
	apt-get install software-properties-common
	apt-add-repository universe
	apt-get update
	apt-get install python-pip
	pip install --upgrade pip

# Install some prerequisites for llvmlite
install_pre:
	apt-get install python-dev
	pip install enum34
	pip install pycosat
	pip install pyyaml
	pip install requests
	pip install ruamel.yaml
	apt-get install zlib1g-dev lib32z1-dev

# Make the compiler libraries
make_libs:
	apt-get install nasm
	cd ./edsger_lib; bash libs.sh; bash make_new_delete_lib.sh; cd ../

# Install NumPy
install_numpy:
	pip install numpy

# Install the PLY library
install_ply: unzip_ply
	cd ./ply-3.8; python setup.py install
	rm ply-3.8.tar.gz

# Unzip the downloaded file
unzip_ply: download_ply
	tar xvfz ply-3.8.tar.gz

# Download the compressed PLY library
download_ply:
	wget https://pypi.python.org/packages/source/p/ply/ply-3.8.tar.gz#md5=94726411496c52c87c2b9429b12d5c50

# Make the compiler executable
make_comp:
	cp ./edsger_compiler/edsc.sh ./edsc
	chmod +x edsc

# Check installation
check_install:
	bash ./edsger_compiler/check_installation.sh

clean:
	cd ./edsger_compiler; rm -f nodes.pyc lexer.pyc lextab.py parser.out parser.pyc parsetab.*; cd ../

distclean:
	cd ./edsger_compiler; rm -f nodes.pyc lexer.pyc lextab.py parser.out parser.pyc parsetab.*; cd ../; rm -f edsc
	cd ./edsger_lib; rm -f lib.a libnewdelete.a; cd ../
