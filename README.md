![cover photo](cover_photo.png)

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

- Then, `docker-compose up`

### Bot instructions

- To get the bot to join a server you need [this URL](https://discord.com/oauth2/authorize?client_id=1206957246743973979&permissions=36700160&scope=bot). Replace `client_id` with your own discord bot's.
- If the bot has been added to the server via the URL, then `/help` will print all available commands.

### Production notes

- `docker compose up --force-recreate --pull always -d`

### Experiments

- Issue with music videos being the first result for queries. Trying out adding `audio` string to youtube-dl search query when using spotify URLs e.g. "50 Cent Candy Shop Audio".
