printf "`cat sonarr-bot.service.format`" $SUDO_USER `pwd` `pwd` > sonarr-bot.service
cp sonarr-bot.service /usr/lib/systemd/system/
chmod 777 /usr/lib/systemd/system/sonarr-bot.service