import json
import os
import re
import requests


from enum import Enum
from types import SimpleNamespace


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Global parameters defining the state of HomeLights
LightsOn: bool = False
LightsBrightness: int = 5


def chatGptCompleteShort(prompt: str):
    """ Rest call to ChatGPT API to return a short and consistent answer on a prompt."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 10
    }
    headers = {"Content-Type": "application/json",
               "Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.post("https://api.openai.com/v1/chat/completions",
                             json=data, headers=headers)
    if(response.status_code != 200):
        return "ERROR"
    else:
        json_data = response.text
        resp = json.loads(
            json_data, object_hook=lambda d: SimpleNamespace(**d))
        return resp.choices[0].message.content


class LightAction(Enum):
    LIGHT_ON = 1
    LIGHT_OFF = 2
    SET_BRIGHTNESS = 3


class LightCommand():

    def __init__(self, action: LightAction, param=None):
        self.action = action
        self.param = param

    def __str__(self):
        paramPart = (f"={self.param}") if self.param != None else ""
        return f"Command: {self.action}{paramPart}"

def extract_brightness(string):
    pattern = r"SET_BRIGHTNESS=(\d+)"
    match = re.search(pattern, string)
    if match:
        return int(match.group(1))
    else:
        return None

def interpretLightsCommand(propmt: str):
    LIGHTS_COMMAND_TEMPLATE = """
  Choose which of these 4 actions 
  ('LIGHTS_ON', 'LIGHTS_OFF', 'SET_BRIGHTNESS=<number>'),
  where <number> can be from 0 to 10 the following text most likely
    asks me to do: '%s', the current BRIGHTNESS_LEVEL=%d
  """
    command_guess = chatGptCompleteShort(
        LIGHTS_COMMAND_TEMPLATE % (propmt, LightsBrightness))
    if 'None' in command_guess or 'none' in command_guess:
        return None
    elif 'LIGHTS_ON' in command_guess:
        return LightCommand(LightAction.LIGHT_ON)
    elif 'LIGHTS_OFF' in command_guess:
        return LightCommand(LightAction.LIGHT_OFF)
    
    brightness=extract_brightness(command_guess)
    if brightness != None:
      return LightCommand(LightAction.SET_BRIGHTNESS, brightness)
    return None

def executeLightCommand(command: LightCommand):
  global LightsOn, LightsBrightness  
  if command.action == LightAction.LIGHT_ON:
    LightsOn=True
  elif command.action == LightAction.LIGHT_OFF:
    LightsOn=False
  elif command.action == LightAction.SET_BRIGHTNESS:
    LightsBrightness=command.param



def main():
  print("Welcome to the LightsControl example!\n")
  while True:
      print("Currently lights are: %s with brightness set to %d\n" %
            (("ON" if LightsOn else "OFF"), LightsBrightness))
      prompt = input()
      command = interpretLightsCommand(prompt)      
      print(command)
      if(command != None):
        executeLightCommand(command)
      else:
        print("I don't understand the command")


main()