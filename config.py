import os
from dotenv import load_dotenv

load_dotenv()

WHM_USERNAME = os.getenv("WHM_USERNAME")

SERVERS = [            os.getenv('SERVER1').replace('https://', '').replace('/', ''),
            os.getenv('SERVER2').replace('https://', '').replace('/', ''),
            os.getenv('SERVER3').replace('https://', '').replace('/', '')]
PASSWORDS = {
           os.getenv('SERVER1').replace('https://', '').replace('/', ''): os.getenv('SERVER1_PASSWORD'),
           os.getenv('SERVER2').replace('https://', '').replace('/', ''): os.getenv('SERVER2_PASSWORD'),
           os.getenv('SERVER3').replace('https://', '').replace('/', ''): os.getenv('SERVER3_PASSWORD')
           }

BALE_TOKEN = os.getenv("BALE_BOT_TOKEN")
BALE_CHANNEL_ID = os.getenv("BALE_CHANNEL_ID")