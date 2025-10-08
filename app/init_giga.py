from utils.gigachat_client import GigaChatClient
import json

with open('json/config.json') as config:
        data = json.load(config)

GIGA_TOKEN = data['gigatoken']

giga = GigaChatClient(credentials=GIGA_TOKEN)