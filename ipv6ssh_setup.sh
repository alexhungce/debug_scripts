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
