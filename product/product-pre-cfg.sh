#!/bin/bash
cp -a win32.win32.x86_64/eclipse/. ../miniEclipse
cd ../
cd product
if [ ! -f "portal.conf" ]; then
echo "The file 'portal.conf' is not exist in ${cdir}."
else
cp portal.conf ../portal/repo/static
echo "copy portal.conf finished"
cd ../portal
if [ -f "portal.db" ];then
rm portal.db
echo "remove portal.db finished"
fi
cd ../portal
python manage.py syncdb
python setup.py
fi
read -n1 -p "Press any key to continue..."
