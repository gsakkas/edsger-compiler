#!/bin/bash
OUTPUT_FILE="a.out"
OPTIMIZE=""
FINAL_CODE=false
INTER_CODE=false

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        -O)
        OPTIMIZE="-O=3"
        shift
        ;;
        -f)
        FINAL_CODE=true
        shift
        ;;
        -i)
        INTER_CODE=true
        shift
        ;;
        *)
        INPUT_FILE=$key
        shift
        ;;
    esac
done

if [[ $INTER_CODE == true || $FINAL_CODE == true ]]; then
    INPUT_FILE=".__read_from_stdin_test__"
    if [ -f $INPUT_FILE ]; then
        rm $INPUT_FILE
    fi
    INTER_FILE="$INPUT_FILE.imm"
    FINAL_FILE="$INPUT_FILE.asm"
    while read line
    do
        echo "$line" >> $INPUT_FILE
    done < "/dev/stdin"
    python ./edsger_compiler/ir.py $INPUT_FILE $INTER_FILE &&
    llc-3.8 -mtriple="x86_64-unknown-gnulinux" $OPTIMIZE $INTER_FILE -o $FINAL_FILE &&
    clang-3.8 $FINAL_FILE ./edsger_lib/lib.a ./edsger_lib/libnewdelete.a -o $OUTPUT_FILE &&
    if [[ $INTER_CODE == true ]]; then
        echo "================= Intermediate Code ================="
        cat $INTER_FILE
        rm $INTER_FILE
    fi &&
    if [[ $FINAL_CODE == true ]]; then
        echo "==================== Final Code ====================="
        cat $FINAL_FILE
        rm $FINAL_FILE
    fi &&
    rm $INPUT_FILE &&
    exit 0
elif [[ -z $INPUT_FILE ]]; then
    echo "No input file or function parameters"
    echo "Usage: ./edsc.sh [-O] [-i] [-f] <file>"
    exit 1
elif [ -f $INPUT_FILE ]; then
    OUTPUT_FILE="${INPUT_FILE%.*}"
    INTER_FILE="$OUTPUT_FILE.imm"
    FINAL_FILE="$OUTPUT_FILE.asm"
    python ./edsger_compiler/ir.py $INPUT_FILE $INTER_FILE &&
    llc-3.8 -mtriple="x86_64-unknown-gnulinux" $OPTIMIZE $INTER_FILE -o $FINAL_FILE &&
    clang-3.8 $FINAL_FILE ./edsger_lib/lib.a ./edsger_lib/libnewdelete.a -o $OUTPUT_FILE &&
    exit 0
else
    echo "No such file: \"$INPUT_FILE\"" &&
    echo "Usage: ./edsc.sh [-O] [-i] [-f] <file>"
    exit 1
fi

