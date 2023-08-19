#!/bin/bash
#Zaleznoscia jest pakiet clonepi
set +e
set +x

# Ustawienie zmiennej środowiskowej z aktualną datą w odpowiednim formacie
MR_DATE=$(date +[%d-%m-%y])

# Wywołanie polecenia clonepi z wykorzystaniem zmiennej MR_DATE
/usr/local/sbin/clonepi /media/pi/SSD/auto-backup/pi-backup.img.gz --compress-file --trim-source --script --quiet --ignore-warnings >> /var/log/clonepi.log 2>&1
mv /media/pi/SSD/auto-backup/pi-backup.img.gz /media/pi/SSD/auto-backup/$MR_DATE-pi-backup.img.gz

# Usuwa pliki starsze niż 35 dni

find /media/pi/SSD/auto-backup/ -type f -mtime +35 -exec rm {} +
