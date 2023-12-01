import settings
from discord.ext import commands
import discord
import requests
import json
import pickle
from datetime import datetime

logger = settings.logging.getLogger("bot")

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
channel = None
scheduler_cog = None
emoji_high_voltage = '\U000026A1';
areas_info = {}
current_subscriptions = {}
last_search_results = {}

# METHODS #

async def add_subscription(subscription):
    await scheduler_cog.update_current_subscriptions(subscription)

async def check_loadshedding(stage):
    logger.debug(f"Execute check_loadshedding for stage: {stage}")
    now = datetime.now()
    today = now.strftime('%A')
    for sub in current_subscriptions:
        area_id = current_subscriptions[sub]['area']['id']
        if 'error' in areas_info[area_id]:
            logger.error(f"Error fetching schedules for: {areas_info[area_id]}")
            await channel.send(f"The latest schedules could not be fetched due to reaching your quota limit.\nYou can check your current quota usage using the '!quota' command.")
            return
        days = areas_info[area_id]['schedule']['days']
        for day in days:
            if len(day['stages']) <= 4 and stage >= 4:
                logger.debug(f"No schedules for stages 5-8 for {area_id}. Using stage 4 schedule.")
                stage = 4
            if day['name'] == today:
                times = day['stages'][stage]
                for time in times:
                    hour = int(time.split(':')[0])
                    if (now.hour < hour and hour - now.hour <= 1):
                        await send_alert(current_subscriptions[sub])

async def load_subscriptions():
    global current_subscriptions, areas_info
    logger.debug("Loading subscriptions")
    try:
        with open(settings.FILE_PATH, 'rb') as stored_subscriptions:
            current_subscriptions = pickle.load(stored_subscriptions)            
            logger.info(f'Pickle file already exists. Loaded data: {current_subscriptions}')
    except FileNotFoundError:
        logger.warn(f'Pickle file does not exist. Subscribing to an area will create a new file and store the subscription.')
    else:
        scheduler_cog.set_current_subscriptions(current_subscriptions)
        areas_info = await scheduler_cog.get_areas_info()
        logger.info("Finished loading subscriptions")

async def remove_subscription(subscription):
    await scheduler_cog.update_current_subscriptions(subscription, delete=True)

def save_subscriptions():
    logger.info("Saving current subscriptions")
    with open(settings.FILE_PATH, 'wb') as stored_subscriptions:
        pickle.dump(current_subscriptions, stored_subscriptions)

async def send_alert(sub):
    await channel.send(f"{sub['user']['mention']}\nLoadshedding starting soon for area: {sub['area']['name']}")

# API CALLS #

async def get_area(area_id):
    try:
        response = requests.get(settings.URLS['area'].format(area=area_id), headers=settings.HEADERS).json()
    except requests.exceptions.HTTPError as e:
        message = json.loads(e.response.text).get('error', 'No error message found')
        logger.error(f"HTTP error: {e.response.status_code}\n{message}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e.response.status_code}\n{e.response.text}")
    except Exception as e:
        logger.error(f"An exception occured: {e}")      
    else:
       return response

async def get_quota():
    try:
        response = requests.get(settings.URLS['api_allowance'], headers=settings.HEADERS).json()     
    except requests.exceptions.HTTPError as e:
        message = json.loads(e.response.text).get('error', 'No error message found')
        logger.error(f"HTTP error: {e.response.status_code}\n{message}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e.response.status_code}\n{e.response.text}")
    except Exception as e:  
        logger.error(f"An exception occured: {e}")
    else:
        return response

async def get_search(search_query):
    try:
        response = requests.get(settings.URLS['areas_search'].format(text=search_query), headers=settings.HEADERS).json()
    except requests.exceptions.HTTPError as e:
        message = json.loads(e.response.text).get('error', 'No error message found')
        logger.error(f"HTTP error: {e.response.status_code}\n{message}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e.response.status_code}\n{e.response.text}")
    except Exception as e:
        logger.error(f"An exception occured: {e}")
    else:
        return response

# EVENTS #

@bot.event
async def on_ready():
    global channel, scheduler_cog
    channel = bot.get_channel(settings.DISCORD_CHANNEL_SECRET)
    
    bot.tree.copy_global_to(guild=settings.GUILDS_ID_SECRET)
    await bot.tree.sync(guild=settings.GUILDS_ID_SECRET)

    await bot.load_extension("scheduler")
    scheduler_cog = bot.get_cog('Scheduler')

    await load_subscriptions()
    scheduler_cog.start_loop_get_eskom_status()
    scheduler_cog.start_loop_get_areas_info()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Sorry, the command '{ctx.message.content[len(ctx.prefix):]}' does not exist. Please check the command syntax.")

@bot.event
async def on_load_areas(data):
    global areas_info
    areas_info = data;

@bot.event
async def on_stage_check(stage):
    await check_loadshedding(stage-1)

@bot.event
async def on_update_current_subscriptions(updated_subscriptions):
    global current_subscriptions
    current_subscriptions = updated_subscriptions
    save_subscriptions()

# COMMANDS #

@bot.tree.command(description="Add a new subscription", name="add")
async def add(interaction: discord.Interaction, area_number: str):
    selected_area = int(area_number)
    user = {'id': interaction.user.id, 'name': interaction.user.name, 'mention': interaction.user.mention}
    area = last_search_results[selected_area]
    subscription = {'user' : user, 'area': area}
    await add_subscription(subscription)
    await interaction.response.send_message(f"{subscription['user']['mention']}\nNew subscription added for: {area['name']}")
    stage = await scheduler_cog.get_eskom_status()
    await check_loadshedding(stage-1)

@bot.tree.command(description="Get area info using an area ID", name="area")
async def area(interaction: discord.Interaction, area_id: str):
    data = await get_area(area_id)

    info, events = data['info'], data['events']
    next_event = events[0] if events else None

    await interaction.response.send_message(f"Area: {info['name']}\nStatus: {next_event['note']}\nStart: {next_event['start']}")

@bot.tree.command(description="View daily API usage", name="quota")
async def quota(interaction: discord.Interaction):
    data = await get_quota()

    allowance = data['allowance']

    await interaction.response.send_message(f"Today's quota usage is: {allowance['count']} / {allowance['limit']}")

@bot.tree.command(description="Search areas by keywords", name="search")
async def search(interaction: discord.Interaction, search_text: str):
    global last_search_results

    search_query = '+'.join(search_text.split(" "))
    data = await get_search(search_query)

    areas = data['areas']
    last_search_results = {index + 1: area for index, area in enumerate(areas)}
    output = '\n'.join([f"{index}. {area['name']} - {area['region']}" for index, area in last_search_results.items()])

    await interaction.response.send_message(f"Areas found:\n{output}")
    await interaction.followup.send("To subscribe to alerts for an area, use the '/add' command and provide the area number.\nFor example, '/add 1'")

@bot.tree.command(description="View the results of the last search", name="search_results")
async def search_results(interaction: discord.Interaction):
    if not last_search_results:
        await interaction.response.send_message("No search results available.")
    else:
        output = '\n'.join([f"{index}. {area['name']} - {area['region']}" for index, area in last_search_results.items()])
        await interaction.response.send_message(f"Last search results:\n{output}")
        await interaction.followup.send("To subscribe to alerts for an area, use the '/add' command and provide the area number.\nFor example, '/add 1'")

@bot.tree.command(description="View all current subscriptions", name="view")
async def view(interaction: discord.Interaction):
    if not current_subscriptions:
        await interaction.response.send_message("No subscriptions available.")
    else:
        indexed_subscriptions = {index + 1: (sub_id, sub) for index, (sub_id, sub) in enumerate(current_subscriptions.items())}
        output = '\n'.join([f"{index}. {sub['user']['name']} - {sub['area']['name']}\n\t{sub['area']['id']}" for index, (sub_id, sub) in indexed_subscriptions.items()])
        await interaction.response.send_message(f"Current subscriptions:\n{output}")
        await interaction.followup.send("To remove a subscription, type 'remove' followed by the subscription number.\nFor example, 'remove 1'")

        def check_remove(m):
            return (m.content.startswith("remove") and int(m.content.split(' ')[1]) in indexed_subscriptions)

        msg = await bot.wait_for("message", check=check_remove) 
        selected_subscription = int(msg.content.split(' ')[1])
        if selected_subscription in indexed_subscriptions:
            subscription = indexed_subscriptions[selected_subscription][1]
            await remove_subscription(subscription)
            await interaction.followup.send(f"{subscription['user']['mention']}\nRemoved subscription for: {subscription['area']['name']}")

# ERRORS #

@add.error
async def add(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Input is invalid or empty. Please retry by entering an area number.")

@area.error
async def area(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Input is invalid or empty. Please retry by entering an area ID.")

@search.error
async def search(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Input is invalid or empty. Please retry by entering a search query.")

if (__name__ == "__main__"):
    bot.run(settings.DISCORD_API_SECRET, root_logger=True)