# Edsger Compiler
A compiler for the Edsger programming language.


## Installation of Edsger Compiler

1) Use "sudo -H make" to create Edsger Compiler. This command will
   install all files and programs necessary for the compiler to run
   properly. It will produce the compiler's executable in the same
   directory, named as "edsc".

2) You can always use "make clean" to remove all irrelevant files,
   that the compiler generates automatically when used.

3) You can also use "make distclean" to do the same as (2) and also
   delete the executable of the compiler. To use the compiler again,
   the "sudo -H make" command should be executed again.


## Usage of Edsger Compiler

Run the compiler with the command "./edsc". You can use the following options:

1) "./edsc -i":
   In this case you will be able to write in command line your program (stdin).
   When finished, in the last of line of your program leave a new line and
   then press "Ctrl+D". You will be presented with the Intermediate Code
   in the command line (stdout) and no executable of your program
   will be produced.

2) "./edsc -f":
   In this case you will be able to write in command line your program (stdin).
   When finished, in the last of line of your program leave a new line and
   then press "Ctrl+D". You will be presented with the Final Code (assembly code)
   in the command line (stdout) and no executable of your program
   will be produced.
3) "./edsc -i -f":
   This case combines those of (1) and (2).

4) "./edsc <file>":
   In this case you will be able to compile a file named "<file>". The executable
   will be in the same directory that the source code was and alongside two more
   files will be created. They will have the same file name as "<file>" but
   different extensions. The first one will have a ".imm" extension and will
   contain the Intermediate Code and the second one will have a ".asm" extension
   and will contaion the Final Code.

5) "./edsc [-i] [-f] <file>":
   If alongside with the parameters "-i" and "-f" a filename is given, it will
   be ignored and one case from (1), (2) or (3) will be executed depending on
   the given parameters.

6) "./edsc -O [...]"
   This case can be combined with all the above. If used the Final Code will be
   optimized. The optimization used is LLVM's -O=3 level.


## Edsger Compiler's files

The Edsger Compiler comes with the following folders:

1) "./edsger_compiler/"
   This folder contains all the programs we wrote that are necessary for the compiler
   to run. It also contains some tests that the installation process uses to check
   if the compiler was installed properly.

2) "./edsger_lib/"
   This folder contains all the programs and files needed for the Edsger libaries.