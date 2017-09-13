#!/bin/bash
if [ -f libnewdelete.a ]
	then
		rm libnewdelete.a
fi
gcc -Wall -c __new_delete__.c
ar -cvq libnewdelete.a __new_delete__.o
rm __new_delete__.o