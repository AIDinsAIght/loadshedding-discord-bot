### Setup

_Python version 3.10+ recommended_

1. Clone the repo
   ```sh
   git clone https://github.com/AIDinsAIght/loadshedding-discord-bot.git
   ```
2. Open the project directory
   * Create a copy of the ```.env.example``` file and name it ```.env```
   * Create a folder named ```logs```
   * Install the required modules
     ```sh
     pip install requirements.txt
     ```
3. Go to https://eskomsepush.gumroad.com/l/api
   * Select a subscription plan (the free plan will work fine)
   * Paste the API token in the ```.env``` file
     ```py
     ESP_API_TOKEN = '<api_token>'
     ```
4. In the Discord client, enable developer mode under _User Settings > Advanced > Developer Mode_
5. Go to the Discord developer portal at https://discord.com/developers
   * Add a new application
   * Go to the _Bot_ section and add a new bot
     * Make sure _Requires OAuth2 Grant Code_ is not enabled
     * Enable all the options under _Privileged Gateway Intents_
     * Under _Bot Permissions_, select _Administrator_
     * Paste the Bot token in the ```.env``` file
       ```py
       DISCORD_API_TOKEN = '<bot_token>'
   * Go to the _OAuth2 > URL Generator_ section
     * Under _Scopes_, select _bot_
     * Under _Bot Permissions_, select _Administrator_
     * Copy the generated URL and paste it in a browser
     * Follow the prompts to add the bot to a server
6. In the Discord client, find the server that the bot was added to, right-click the server icon, and copy the server ID
   * Paste the server ID in the ```.env``` file
     ```py
     GUILDS_ID = <server_id>
     ```
 8. In the Discord client, find the channel the bot will use, right-click the channel name, and copy the channel ID
    * Paste the channel ID in the ```.env``` file
      ```py
      DISCORD_CHANNEL_ID = <channel_id>
      ```
7. Run ```bot.py```
