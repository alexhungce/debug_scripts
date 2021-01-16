#!/bin/bash
# Copyright (C) 2020-2021 Canonical
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

ACPI_DIR="/sys/firmware/acpi/tables"
OUTPUT_FILE="$PWD/acpidump.log"

dump_acpi_tables () {

	cd $1
	for table in * ; do
		if [ -f $table ] ; then
			acpidump -f $table >> $2
		elif [ -d $table ] ; then
			pushd . &> /dev/null
			dump_acpi_tables $table $OUTPUT_FILE
			popd &> /dev/null
		fi
	done
}

if [ $EUID -ne 0 ]; then
	echo "`basename $0`: must be executed with sudo"
	exit 1
fi

if [ -f $OUTPUT_FILE ]; then
	echo "`basename $OUTPUT_FILE`: file already exists"
	exit 2
fi

if ! [ -z "$1" ]; then
	ACPI_DIR=$1
fi

if ! [ -f $ACPI_DIR/DSDT ] ; then
	echo "Not an ACPI table directory"
	exit 3
fi

pushd . &> /dev/null
dump_acpi_tables $ACPI_DIR $OUTPUT_FILE
popd &> /dev/null

# add permissions to non-root
sudo chmod 666 $OUTPUT_FILE


