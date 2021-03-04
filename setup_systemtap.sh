#!/bin/bash
# Copyright (C) 2021 Canonical
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

# configure for systemtap and debug symbols
sudo apt install -y ubuntu-dbgsym-keyring
printf "deb http://ddebs.ubuntu.com %s main restricted universe multiverse\n" $(lsb_release -cs){,-updates,-proposed} | \
	sudo tee -a /etc/apt/sources.list.d/ddebs.list

sudo apt update && sudo apt install -y git build-essential linux-image-`uname -r`-dbgsym


# install systemtap from source
pushd .
sudo sed -i '4,25s/# deb-src/deb-src/' /etc/apt/sources.list
sudo apt build-dep -y systemtap && git clone git://sourceware.org/git/systemtap.git
cd systemtap && autoreconf -ivf && ./configure && make all -j `getconf _NPROCESSORS_ONLN` && sudo make install
popd

# Clone systemtab scripts
git clone https://github.com/alexhungce/pmdebug
