#!/bin/bash
TEST_DIR=/tmp/testxb

#create test directory on tmpfs not to be limited by HD speed, 
# on my NTB it gives about 3.8GB/s write speed
#

mkdir $TEST_DIR
sudo mount -t tmpfs tmpfs $TEST_DIR
 

#create 1GB random file
RAND_FILE=$TEST_FILE/randfile
dd if=/dev/urandom bs=1MB count=1024 of=$RAND_FILE

# test cp speed
echo "Testing cp speed"
sync
DUR=`/usr/bin/time -f %e cp /tmp/testxb/randfile /tmp/testxb/copied 2>&1`
sync
SPEED=`echo "scale=2; 1000 / $DUR"|bc`
echo "cp speed is $SPEED MB/s"
rm /tmp/testxb/copied

# sudo umount $TEST_DIR
# rm -r $TEST_DIR
 