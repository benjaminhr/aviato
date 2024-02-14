<img src='cover_photo.png' width='512'>

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

### Bot instructions

- `/join` whilst you are in the voice channel of a server, to let the bot join the voice channel as well
- `/play <spotify-url | youtube-url>`
- `/leave`

### Experiments

- Issue with music videos being the first result for queries. Trying out adding `audio` string to youtube-dl search query when using spotify URLs e.g. "50 Cent Candy Shop Audio".
