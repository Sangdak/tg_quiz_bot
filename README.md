# Bots for quizzes in Telegram messenger and social network "Вконтакте".

## About

This project provides an opportunity to conduct a personal quiz by a user through a dialog with a bot in the messenger Telegram or in the social network Vkontakte.

## Setup

In order to avoid problems caused by blocking requests to redis service from ip addresses belonging to the Russian Federation segment, it is recommended to deploy the repository on your device.

1. docker, docker-compose and git must be installed on your system.
2. Copy the repository:
```sh
git clone <repository link>
```
4. Use the command line to navigate to the directory with the project files.
5. Create and activate virtual environment (if necessary) and install the project dependencies.
```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
6. Demonize running scripts through systemd:
```sh
sudo nano /etc/systemd/system/vk_bot.service
```
File content:
```sh
	[Unit]
	Description=<имя_сервиса>
	After=docker.service
    Requires=docker.service
	 
	[Service]
	User=deepak
	Group=admin
	Type=simple
	Restart=always
	ExecStart=<absolute path to your venv>/bin/python3 <absolute path to your script> (.../tg_bot.py or .../vk_bot.py)
	 
	[Install]
	WantedBy=multi-user.target
```
Repeat the same with a second file:
```sh
sudo nano /etc/systemd/system/tg_bot.service
etc ...
```
7.Create '.env' file:
```sh
sudo nano .env
```

```sh

    TG_TOKEN - <your TG bot token>. instructions: https://medium.com/spidernitt/how-to-create-your-own-telegram-bot-63d1097999b6
    VK_TOKEN - <your Vk-api bot token> 
    REDIS_HOST - localhost (default)
    REDIS_PORT - 6379 (default)
    REDIS_DATABASES = 0

```

## Launch

1. Start redis-container through docker-compose:
```sh
docker-compose up -d
```
2. Enable and run both services:
```sh
sudo systemctl enable vk_bot.service
sudo systemctl start vk_bot.service

sudo systemctl enable tg_bot.service
sudo systemctl start tg_bot.service
```

In test mode, the bots are up and running:
- VK: https://vk.com/club215578482 (write a private message to the group)
- TG: https://t.me/ed_space_photos_bot

## Project Goals

The code was written for educational purposes in an online course for web developers [Devman](https://dvmn.org).