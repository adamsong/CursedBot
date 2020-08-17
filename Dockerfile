FROM docker.pkg.github.com/adamsong/cursedbot/deps:v1.0.3
COPY bot /bot
  
ENTRYPOINT [ "/usr/local/bin/python", "-mbot.bot" ]