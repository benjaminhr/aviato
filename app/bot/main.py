from lib import commands 
from lib import config
from lib import events

if __name__ == "__main__":
  commands.bot.run(config.discord_token)