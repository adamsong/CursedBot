FROM python:3.7.6-alpine3.10
COPY bot /bot
RUN apk add --no-cache gcc
RUN python3 -m pip install -U discord.py[voice]
ENTRYPOINT [ "/usr/local/bin/python", "/bot/bot.py" ]