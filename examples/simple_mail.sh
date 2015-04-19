#!/bin/sh
IPF="/tmp/.ip"
MAIL="YOUR MAIL ADDRESS"

ip=$1
echo $ip > $IPF

mail -s "WANIP" $MAIL < $IPF
