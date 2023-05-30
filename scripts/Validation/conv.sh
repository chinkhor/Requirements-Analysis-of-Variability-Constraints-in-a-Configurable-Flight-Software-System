#!/bin/bash
T='true'
F='false'
null=''
filename="cfs_time_map"
declare -A featuremap
while read line; do
	set -- $line
	featuremap[${1}]=${2}
done < $filename
#for i in ${!featuremap[@]}; do
#	echo $i ${featuremap[$i]}
#done
if ! test -d "config"; then
       mkdir config	
fi
for i in {1..112}; do
	lzero='0'
	len=`expr 5 - ${#i}`
	for (( j=1; j<$len ; j++ )); do
		lzero="0$lzero"
	done
	filename="products/$lzero$i.xml"
	output_file="config/cfg$i"
	#echo "reading fle $filename"
	while read line; do
		set -- $line
		if [[ $line == *'"selected"'* ]]; then
			feature=$(cut -d '"' -f2 <<< "$3")
			if [[ ${featuremap[$feature]} != $null ]]; then
				echo "${featuremap[$feature]} $T" >> $output_file
			fi
		fi
		if [[ $line == *'"unselected"'* ]]; then
			feature=$(cut -d '"' -f2 <<< "$3")
			if [[ ${featuremap[$feature]} != $null ]]; then
				echo "${featuremap[$feature]} $F" >> $output_file
			fi
		fi
	done < $filename
done
