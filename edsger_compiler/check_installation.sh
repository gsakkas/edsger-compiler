#!/bin/bash

TEST_PATH=./edsger_compiler/tests

echo "Checking installation..."
echo
for i in {1..4}
do
	echo "Testcase $i out of 4:" 
	./edsc -O $TEST_PATH/test_$i.eds
	./$TEST_PATH/test_$i > $TEST_PATH/test_temp_$i
	if ( diff $TEST_PATH/test_temp_$i $TEST_PATH/test_output_$i > .__testing__) then
		echo "OK!"
	else
		echo "Something went wrong with this testcase only!"
		echo
		echo "Exiting..."
		rm .__testing__ $TEST_PATH/test_$i $TEST_PATH/test_$i.imm $TEST_PATH/test_$i.asm $TEST_PATH/test_temp_$i
		exit 1
	fi
	rm .__testing__ $TEST_PATH/test_$i ./$TEST_PATH/test_$i.imm $TEST_PATH/test_$i.asm $TEST_PATH/test_temp_$i
done
echo
echo "Installation is complete!"
exit 0