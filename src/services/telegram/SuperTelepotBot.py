import telepot
import requests

class SuperTelepotBot(telepot.Bot):
    """
    Wrapper class on Telepot.Bot to support new commands
    due to discontinued python library
    """
    
    def __init__(self, token):
        super().__init__(token)

    def setCommands(self, commands: dict):
        """
        example of commands:
        {
        "commands": [
            {
            "command": "start",
            "description": "Start using bot"
            },
            {
            "command": "help",
            "description": "Display help"
            },
            {
            "command": "menu",
            "description": "Display menu"
            }
        ],
        "language_code": "en"
        }
        """

        r = requests.get(f"https://api.telegram.org/bot{self._token}/setMyCommands", json=commands)
        return r.status_code == 200