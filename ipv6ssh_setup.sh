#!/bin/bash
# Copyright (C) 2016-2020 Canonical
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

sudo apt-get install -y miredo tor pastebinit openssh-server
sudo systemctl restart miredo

cat << EOF >> ~/.ssh/config
Host *.onion
  ProxyCommand /bin/nc.openbsd -xlocalhost:9050 -X5 %h %p
EOF

sudo systemctl restart tor
#TODO enable tor hidden service
#TODO get hostname - cat /var/lib/tor/hidden_service/hostname


echo ""
echo "== pastebin url == "
ip address | pastebinit
