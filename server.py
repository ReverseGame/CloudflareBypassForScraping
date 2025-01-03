import json
import re
import os
import uuid
from urllib.parse import urlparse

from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Dict
import argparse

from base64_utils import check_base64_string
from file_utils import generate_proxy_extension, del_user_data_dir
from multiprocessing import freeze_support

#pyinstaller --onefile --add-data "Chrome-proxy-helper;Chrome-proxy-helper" server.py
# Check if running in Docker mode
DOCKER_MODE = os.getenv("DOCKERMODE", "false").lower() == "true"

# Chromium options arguments
arguments = [
    # "--remote-debugging-port=9222",  # Add this line for remote debugging
    "-no-first-run",
    "-force-color-profile=srgb",
    "-metrics-recording-only",
    "-password-store=basic",
    "-use-mock-keychain",
    "-export-tagged-pdf",
    "-no-default-browser-check",
    "-disable-background-mode",
    "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
    "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
    "-deny-permission-prompts",
    "-disable-gpu",
    "-accept-lang=en-US",
    #"-incognito" # You can add this line to open the browser in incognito mode by default 
]

browser_path = "/usr/bin/google-chrome"
app = FastAPI()

log = False
# Pydantic model for the response
class CookieResponse(BaseModel):
    cookies: Dict[str, str]
    user_agent: str


# Function to check if the URL is safe
def is_safe_url(url: str) -> bool:
    parsed_url = urlparse(url)
    ip_pattern = re.compile(
        r"^(127\.0\.0\.1|localhost|0\.0\.0\.0|::1|10\.\d+\.\d+\.\d+|172\.1[6-9]\.\d+\.\d+|172\.2[0-9]\.\d+\.\d+|172\.3[0-1]\.\d+\.\d+|192\.168\.\d+\.\d+)$"
    )
    hostname = parsed_url.hostname
    if (hostname and ip_pattern.match(hostname)) or parsed_url.scheme == "file":
        return False
    return True


# Function to bypass Cloudflare protection
async def bypass_cloudflare(url: str, proxy: str, user_data_dir: str, retries: int, log: bool) -> ChromiumPage:
    from pyvirtualdisplay import Display

    if DOCKER_MODE:
        # Start Xvfb for Docker
        display = Display(visible=0, size=(1920, 1080))
        display.start()

        options = ChromiumOptions()
        options.set_argument("--auto-open-devtools-for-tabs", "true")
        options.set_argument("--remote-debugging-port=9222")
        options.set_argument("--no-sandbox")  # Necessary for Docker
        options.set_argument("--disable-gpu")  # Optional, helps in some cases
        options.set_paths(browser_path=browser_path).headless(False)
    else:
        options = ChromiumOptions()
        # options.set_argument("--auto-open-devtools-for-tabs", "true")
        options.set_paths(browser_path=browser_path).headless(False)
        options.set_argument(f"--user-data-dir={user_data_dir}")
        options.set_argument(f"--window-size=800,600")
        options.set_argument(f"--disable-timeouts-for-profiling")
        options.auto_port()
        if proxy:
            extension_path = generate_proxy_extension(proxy, user_data_dir)
            options.add_extension(extension_path)

    driver = ChromiumPage(addr_or_opts=options, timeout=30)
    try:
        driver.get(url, timeout=10)
        cf_bypasser = CloudflareBypasser(driver, retries, log)
        await cf_bypasser.bypass()
        return driver
    except Exception as e:
        driver.quit()
        if DOCKER_MODE:
            display.stop()  # Stop Xvfb
        raise e


# Endpoint to get cookies
@app.get("/cookies", response_model=CookieResponse)
async def get_cookies(url: str, proxy: str = None, retries: int = 5):
    if not is_safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    try:
        user_data_dir = str(uuid.uuid4())
        driver = await bypass_cloudflare(url, proxy, user_data_dir, retries, log)
        cookies = driver.cookies(as_dict=True)
        user_agent = driver.user_agent
        driver.quit()
        del_user_data_dir(user_data_dir)
        return CookieResponse(cookies=cookies, user_agent=user_agent)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to get HTML content and cookies
@app.get("/html")
async def get_html(url: str, proxy: str = None, retries: int = 5):
    if not is_safe_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL")
    try:
        user_data_dir = str(uuid.uuid4())
        driver = bypass_cloudflare(url, proxy, user_data_dir, retries, log)
        html = driver.html
        cookies_json = json.dumps(driver.cookies(as_dict=True))

        response = Response(content=html, media_type="text/html")
        response.headers["cookies"] = cookies_json
        response.headers["user_agent"] = driver.user_agent
        driver.quit()
        del_user_data_dir(user_data_dir)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


SERVER_PORT = 12306
# Main entry point
if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: python server.py [hash]")
    # else:
    #     hash = sys.argv[1]
    #     print(f"Server started on port {SERVER_PORT} with hash {}")
    #     if hash and check_base64_string(hash, str(SERVER_PORT), 10 * 100000000000000):
    freeze_support()  # 添加这一行
    import uvicorn
    # if args.headless and not DOCKER_MODE:
    #     from pyvirtualdisplay import Display
    #     display = Display(visible=0, size=(1920, 1080))
    #     display.start()
    uvicorn.run("server:app", host="0.0.0.0", port=SERVER_PORT, workers=5)
