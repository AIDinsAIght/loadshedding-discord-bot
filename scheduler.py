from discord.ext import commands, tasks
import json
import requests
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

API_KEY = '6E24BEDA-24A0486E-8E0EAB87-314DEEFE'
HEADERS = {'token': API_KEY}
URLS = {
    'area': 'https://developer.sepush.co.za/business/2.0/area?id={area}',
    'eskom_status': 'https://loadshedding.eskom.co.za/LoadShedding/GetStatus'
}
TIMEZONE = ZoneInfo('Africa/Johannesburg')
scheduled_time = time(tzinfo=TIMEZONE)
minute_buffer = 30

class Scheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.areas_info = {}
        self.current_subscriptions = {}
        self.loop_get_areas_info.add_exception_type(Exception)
        self.get_eskom_status.add_exception_type(Exception)
    
    def cog_unload(self) -> None:
        self.get_areas_info.stop()
        self.get_eskom_status.stop()
    
    def start_loop_get_areas_info(self):
        self.loop_get_areas_info.start()
    
    def start_get_eskom_status(self):
        self.get_eskom_status.start()

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
                response = requests.get(URLS['area'].format(area=area_id), headers=HEADERS)
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
    
    # LOOPS #

    @tasks.loop(hours=1, reconnect=False)
    async def get_eskom_status(self):
        now = datetime.now()
        next_exec = time(now.hour+1, minute_buffer, tzinfo=TIMEZONE) if now.minute >= minute_buffer else time(now.hour, minute_buffer, tzinfo=TIMEZONE)
        self.get_eskom_status.change_interval(time=next_exec)
        try:
            response = requests.get(URLS['eskom_status'])
            stage = int(response.text)-1
            self.bot.dispatch('stage_check', stage)
        except Exception as e:
            print(f"Error fetching eskom status: {e}")
    
    @get_eskom_status.before_loop
    async def before_get_eskom_status(self):
        await self.bot.wait_until_ready()
    
    @tasks.loop(time=scheduled_time, reconnect=False)
    async def loop_get_areas_info(self):
        self.areas_info = await self.get_areas_info()
        self.bot.dispatch('load_areas', self.areas_info)
    
    @loop_get_areas_info.before_loop
    async def before_loop_get_areas_info(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Scheduler(bot))