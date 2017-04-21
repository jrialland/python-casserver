#!/bin/bash

function fix_pip8 {
	for f in $(find ./ -type f -name "*.py"); do
            echo $f
	    cp $f $f~
	    autopep8 -i $f
	    if [ "$?" -eq "0" ]; then
		rm $f~
	    else
		mv $f~ $f
	    fi 
	done
}

function add_coding() {
	for f in $(find ./ -type f -name "*.py"); do
	   cat $f | grep 'coding:utf-8 -*-' > /dev/null
	   if [ "$?" -ne "0" ]; then
               cp $f $f~
               echo '# -*- coding:utf-8 -*-' > $f
               cat $f~ >> $f
               rm $f~
           fi
        done
}

fix_pip8
add_coding
