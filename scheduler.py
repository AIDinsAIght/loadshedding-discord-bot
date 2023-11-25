import settings
from discord.ext import commands, tasks
import json
import requests
from datetime import datetime, time

scheduled_time = time(tzinfo=settings.TIMEZONE)
minute_buffer = 30

class Scheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.areas_info = {}
        self.current_subscriptions = {}
        self.loop_get_areas_info.add_exception_type(Exception)
        self.loop_get_eskom_status.add_exception_type(Exception)
    
    def cog_unload(self) -> None:
        self.loop_get_areas_info.stop()
        self.loop_get_eskom_status.stop()
    
    def start_loop_get_areas_info(self):
        self.loop_get_areas_info.start()
    
    def start_loop_get_eskom_status(self):
        self.loop_get_eskom_status.start()

    def set_current_subscriptions(self, subscriptions):
        self.current_subscriptions = subscriptions

    async def update_current_subscriptions(self, subscription, delete=False):
        area_id = subscription['area']['id']
        subscription_id = f"{subscription['user']['id']}_{area_id}"
        self.current_subscriptions.pop(subscription_id, None) if delete else self.current_subscriptions.update({subscription_id: subscription})
        self.areas_info.pop(area_id, None) if delete else self.areas_info.update({area_id: await self.get_area_info(area_id)})
        self.bot.dispatch('update_current_subscriptions', self.current_subscriptions)

    async def get_areas_info(self):
        self.areas_info = {}
        for sub in self.current_subscriptions:
            area_id = self.current_subscriptions[sub]['area']['id']
            self.areas_info[area_id] = await self.get_area_info(area_id)
        return self.areas_info
    
    async def get_area_info(self, area_id):
            try:
                response = requests.get(settings.URLS['area'].format(area=area_id), headers=settings.HEADERS)
                data = response.json()
            except requests.exceptions.HTTPError as e:
                message = json.loads(e.response.text).get('error', 'No error message found')
                await print(f"HTTP error: {e.response.status_code}\n{message}")
            except requests.exceptions.RequestException as e:
                await print(f"Network error: {e.response.status_code}\n{e.response.text}")
            except Exception as e:
                await print(f"An error occured.\nPlease retry, or contact an administrator if the issue persists.")
            else:
                return data;

    async def get_eskom_status(self):
        try:
            response = requests.get(settings.URLS['eskom_status'])
            stage = response.text
        except Exception as e:
            print(f"Error fetching eskom status: {e}")
        else:
            return int(stage)-1
    
    # LOOPS #

    @tasks.loop(hours=1, reconnect=False)
    async def loop_get_eskom_status(self):
        now = datetime.now()
        next_exec = time(now.hour+1, minute_buffer, tzinfo=settings.TIMEZONE) if now.minute >= minute_buffer else time(now.hour, minute_buffer, tzinfo=settings.TIMEZONE)
        self.loop_get_eskom_status.change_interval(time=next_exec)
        stage = await self.get_eskom_status()
        self.bot.dispatch('stage_check', stage)
    
    @tasks.loop(time=scheduled_time, reconnect=False)
    async def loop_get_areas_info(self):
        self.areas_info = await self.get_areas_info()
        self.bot.dispatch('load_areas', self.areas_info)

    # BEFORE LOOPS #
    
    @loop_get_eskom_status.before_loop
    async def before_loop_get_eskom_status(self):
        await self.bot.wait_until_ready()

    @loop_get_areas_info.before_loop
    async def before_loop_get_areas_info(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Scheduler(bot))