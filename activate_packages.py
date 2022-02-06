import asyncio
import json
import logging
import random
import re
import sys
import time

import requests
from ASF import IPC
from tqdm import tqdm

logging.basicConfig(
    filename="logging.txt",
    filemode='w',
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG)

log = logging.getLogger('urbanGUI')

try:
	config = json.load(open("config.json"))
	log.debug("Found config file")
except FileNotFoundError:
	log.debug("Couldn't find config file")
	config = {
	    "IPC": {
	        "host": "http://localhost:1242",
	        "password": "your IPC password"
	    },
	    "STEAM": {
	        "username": "your STEAM username"
	    },
	    "git_token": "NOT needed if only used to activate packages"
	}
	config["IPC"]["host"] = input("Enter your ArchiSteamFarm host address: ")
	config["IPC"]["password"] = input(
	    "Enter your ArchiSteamFarm host password: ")
	config["STEAM"]["username"] = input(
	    "Entering your steam username will download the IDs of the Steam games you own to skip them when activating packages.\nIf you don't want to enter your username just leave it empty and press enter.\nThe steam username is the username in the url when opening your steam profile.\nexample: https://steamcommunity.com/id/Louis_45/ → Louis_45 is the steam username\nYour Steam username:"
	)
	log.debug("Saving config file")
	with open("config.json", "w") as f:
		f.write(json.dumps(config))
	log.debug("Saved config file")
except json.JSONDecodeError:
	log.error("Couldn't decode config to json")
	sys.exit()


async def activatePackages(asf, tries):
	with requests.get(
	    'https://raw.githubusercontent.com/Luois45/claim-free-steam-packages/update-package_list/package_list.txt'
	) as f:
		package_list = f.text.split(',')

	activatedPackage = False
	try:
		with open('activated_packages.txt', 'r') as f:
			activated_packages = f.read().split(',')
	except FileNotFoundError:
		with open('activated_packages.txt', 'w') as f:
			log.info("Created activated_packages file")
			steamUsername = config["STEAM"]["username"]
			if steamUsername != "" and steamUsername != "your STEAM username":
				with requests.get(
				    f"https://steamcommunity.com/id/{steamUsername}/games/?tab=all"
				) as r:
					html = r.text
					regex = re.compile('"appid":(\d+),')
					results = regex.findall(html)
					log.info(
					    f"Fetched {len(results)} packages to acitvated_packages.txt using Steam Username"
					)
					for result in results:
						f.write(result + ",")
		with open('activated_packages.txt', 'r') as f:
			activated_packages = f.read().split(',')

	apps = []
	for app in package_list:
		if not app in activated_packages:
			apps.append(app)
	random.shuffle(apps)
	del activated_packages
	del package_list

	for app in tqdm(apps, desc=f'{tries} attempt: Activating licenses'):

		cmd = "!addlicense app/" + app

		resp = await asf.Api.Command.post(body={'Command': cmd})

		if resp.success:
			log.info(resp.result.replace("\r\n", ""))
			successCodes = ["Items:", "Aktivierte IDs:"]

			if any(x in resp.result for x in successCodes):
				activatedPackage = True
				with open('activated_packages.txt', 'a') as f:
					f.write(app + ",")
		else:
			log.info(f'Error: {resp.message}')
		time.sleep(90)
	return activatedPackage


async def main():
	async with IPC(ipc=config["IPC"]["host"],
	               password=config["IPC"]["password"]) as asf:
		tries = 0
		while True:
			tries += 1
			activatedPackage = await activatePackages(asf, tries)
			if activatedPackage:
				break


loop = asyncio.get_event_loop()
output = loop.run_until_complete(main())
loop.close()
