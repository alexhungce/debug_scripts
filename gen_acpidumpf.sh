#!/bin/bash
# Copyright (C) 2020 Canonical
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

if [ $EUID -ne 0 ]; then
	echo "`basename $0`: must be executed with sudo"
	exit 1
fi

if ! [ -z "$1" ]; then
	ACPI_DIR=$1
fi

if ! [ -f $ACPI_DIR/DSDT ] ; then
	echo "Not an ACPI table directory"
	exit 1
fi

pushd . &> /dev/null

cd $ACPI_DIR
for table in * ; do
	if [ -f $table ] ; then
		acpidump -f $table >> $OUTPUT_FILE
		echo "" >> $OUTPUT_FILE
	fi
done

[ -d dynamic ] || exit 2

cd dynamic
for table in * ; do
	if [ -f $table ] ; then
		acpidump -f $table >> $OUTPUT_FILE
		echo "" >> $OUTPUT_FILE
	fi
done

# add permissions to non-root
sudo chmod 666 $OUTPUT_FILE

popd &> /dev/null

