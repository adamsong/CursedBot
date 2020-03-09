FROM docker.pkg.github.com/adamsong/cursedbot/cursedbot:dependencies
COPY bot /bot
  
ENTRYPOINT [ "/usr/local/bin/python", "/bot/bot.py" ]