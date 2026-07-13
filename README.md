# BearBardBot — Telegram Leveling Bot

A Telegram bot that awards XP for group chat activity, with levels,
leaderboards, and level-up announcements.

## Tech Stack
- Python (python-telegram-bot)
- PostgreSQL (persistent user/XP data)
- Docker + Docker Compose
- Deployed on AWS EC2

## Architecture
- `bot` container — Python bot logic (polling mode)
- `postgres` container — user levels and XP
- Data persisted in Docker volume

## Local Development
1. Clone the repo
2. Create `.env` with BOT_TOKEN and POSTGRES credentials
3. `docker-compose up -d --build`

## Deployment (EC2)
1. SSH into EC2 instance
2. `git clone` this repo
3. Create `.env` with production credentials
4. `docker-compose up -d --build`
5. Docker configured to restart on reboot

## Commands
- `/level` — check your XP and level
- `/rank` — group leaderboard
- `/help` — show commands
