[![Build Status](https://travis-ci.org/ivaniskandar/synology-telegram-bot.svg?branch=master)](https://travis-ci.org/ivaniskandar/synology-telegram-bot)

# Telegram Bot for Synology DiskStation Manager (DSM)

A Docker image based on Alpine Linux that runs [Telegram](https://telegram.org) bot to manage a Synology DiskStation machine.

## Features

Currently support these functions:

### Download Station
* `/mydownloads` - manage your downloads
* `/adddownload` - create a new download task
* `/resumedownloads` - resume all inactive download tasks
* `/pausedownloads` - pause all active download tasks
* `/cleanupdownloads` - clear completed download tasks

### System Info
* `/resourcemonitor` - show NAS resource infos
* `/nasnetwork` - show NAS network status
* `/nashealth` - show NAS health status
* `/bothealth` - show bot health status

## Environment Variables

Make sure to set the container environment variables:

* `BOT_TOKEN` - Your bot's token. Make one with [@BotFather](https://telegram.me/BotFather)
* `BOT_OWNER_ID` - The bot will only respond to user with this ID, get it from [@userinfobot](https://telegram.me/userinfobot)
* `NAS_IP` - Your DiskStation's IP address. Make sure it uses a static IP
* `NAS_PORT` - Your DiskStation's port number. DSM default is 5000
* `DSM_ACCOUNT` - Your DSM account name
* `DSM_PASSWORD` - Your DSM password
* `TZ` - System time zone. See available time zones [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

## Source Code

Available on [Github](https://github.com/ivaniskandar/synology-telegram-bot)
