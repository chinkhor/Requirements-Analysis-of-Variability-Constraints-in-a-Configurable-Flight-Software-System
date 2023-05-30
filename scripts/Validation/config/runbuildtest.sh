#!/bin/bash
T='true'
F='false'
cd ..
if test -e "buildtest.log"; then
	rm buildtest.log
fi
#make SIMULATION=native ENABLE_UNIT_TESTS=true prep
make clean >>buildtest.log
make SIMULATION=native prep >>buildtest.log
cd sample_defs
sed -i "s/CFE_MISSION_TIME_AT_TONE_WAS     true/CFE_MISSION_TIME_AT_TONE_WAS true/g" sample_mission_cfg.h
sed -i "s/CFE_MISSION_TIME_AT_TONE_WAS     false/CFE_MISSION_TIME_AT_TONE_WAS false/g" sample_mission_cfg.h
cd ../config
for n in {1..112}; do
	filename="cfg$n"
	while read line; do
		set -- $line
		directive=$1
		setting=$2
		if ($2 == $T)
		then
			original=$F
		else
			original=$T
		fi
		cd ../sample_defs
		search_str="$directive $original"
		replace_str="$directive $setting"
		sed -i "s/$search_str/$replace_str/g" cpu1_platform_cfg.h
		sed -i "s/$search_str/$replace_str/g" sample_mission_cfg.h
		cd ../config
	done < $filename
	cd ..
	echo "############ Build $filename ########################" >>buildtest.log
	echo >>buildtest.log
	if test -d "build/exe"; then
		rm -r build/exe
	fi
	make install >>buildtest.log 2>&1 
	#make test
	#make lcov
	#lcov_file="lcov_$filename"
	#cp -r build/native/default_cpu1/lcov $lcov_file 
	echo "########### Done Build $filename ###################" >>buildtest.log
	echo >>buildtest.log
	if test -d "build/exe"; then
		echo "Build $filename passed"
	else
		echo "Build $filename failed"
	fi
	cd config
done
