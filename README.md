# aviato

### Discord bot for playing spotify urls via youtube 🤘

- Create a spotify developer account to get client secret and client ID.
- Create a discord bot to get bot token
- Create `.env` file with the following:

```
DISCORD_TOKEN="your token here"
SPOTIFY_CLIENT_SECRET="your secret here"
SPOTIFY_CLIENT_ID="your id here"
```

- `docker build -t aviato .`
- `docker run aviato`

To get the bot to join a server you need the following URL:

- `https://discord.com/oauth2/authorize?client_id=1206957246743973979&permissions=36700160&scope=bot`
