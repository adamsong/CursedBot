FROM docker.pkg.github.com/adamsong/cursedbot/deps:v1.0.0
COPY bot /bot
  
ENTRYPOINT [ "/usr/local/bin/python", "/bot/bot.py" ]