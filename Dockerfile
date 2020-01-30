FROM python:3.7.6-alpine3.10
COPY bot /bot
RUN apk --update add python py-pip openssl ca-certificates py-openssl wget
RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install discord.py[voice] \
  && apk del build-dependencies
  
ENTRYPOINT [ "/usr/local/bin/python", "/bot/bot.py" ]