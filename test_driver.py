import asyncio
import uuid

from file_utils import del_user_data_dir
from server import bypass_cloudflare


async def open_browser():
    user_data_dir = str(uuid.uuid4())
    driver = await bypass_cloudflare('https://www.theconcert.com/concert/3789', 'aazhdgoo:FlsqGTZDzRy@199.67.96.162:61046', user_data_dir, 5, False)
    cookies = driver.cookies(as_dict=True)
    user_agent = driver.user_agent
    print('11111111111111111111')
    # driver.quit()
    print('2222222222222222222222222')
    del_user_data_dir(user_data_dir)


asyncio.run(open_browser())
