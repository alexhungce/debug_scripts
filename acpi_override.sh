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

#!/bin/bash
shopt -s -o nounset

read -p "Please place AML files in $PWD. Press any key to continue..."

if ! grep -q CONFIG_ACPI_TABLE_UPGRADE=y /boot/config-$(uname -r) ; then
	echo "CONFIG_ACPI_TABLE_UPGRADE is not enabled in kernel! Aborting ..."
fi

# backup initrd.img
cp /boot/initrd.img-$(uname -r) .

if [ -d kernel ] ; then
	echo "Directory \"kernel\" exists! Aborting ..."
	exit
elif ! ls *.aml &> /dev/null ; then
	echo "no AML files found! Aborting ..."
	exit
else
	mkdir -p kernel/firmware/acpi
fi

mv *.aml kernel/firmware/acpi
find kernel | cpio -H newc --create > my_tables.cpio
cat my_tables.cpio /boot/initrd.img-$(uname -r) > my_initrd
sudo mv my_initrd /boot/initrd.img-$(uname -r)
rm -r kernel

echo "Please restart to load new ACPI tables... "
