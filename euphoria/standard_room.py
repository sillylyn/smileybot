from . import chat_room
from . import utils
import time
import datetime
import contextlib


class StandardRoom(chat_room.ChatRoom):
    def __init__(self, roomname, password=None, attempts=None):
        super().__init__(roomname, password, attempts)

        self.ping_text = 'Pong!'
        self.short_help_text = None
        self.help_text = None

        self.isPaused = False
        self.isAlive = True

    def handle_message(self, data):
        content = data['data']['content']
        reply = data['data']['id']
        host = False

        with contextlib.suppress(KeyError):
            host = data['data']['sender']['is_manager']

        if self.isPaused:
            if content == '!restore @' + self.nickname():
                self.isPaused = False
                self.start_utc = datetime.datetime.utcnow()
                self.start_time = time.time()
                self.send_chat('/me has been restored.', reply)

        if not self.isPaused:
            if content == '!ping':
                self.send_chat(self.ping_text, reply)
            elif content == '!ping @' + self.nickname:
                self.send_chat(self.ping_text, reply)

            elif content == '!help':
                if self.short_help_text is not None:
                    self.send_chat(self.short_help_text, reply)
            elif content == '!help @' + self.nickname:
                if self.help_text is not None:
                    self.send_chat(self.help_text, reply)

            elif content == '!uptime @' + self.nickname:
                u = datetime.datetime.strftime(self.start_utc, '%Y-%m-%d %H:%M:%S')
                t = utils.extract_time(self.uptime())

                self.send_chat('/me has been up since ' + u + ' UTC (' + t + ')', reply)

            elif content == '!pause @' + self.nickname:
                self.isPaused = True
                self.send_chat('/me has been paused.', reply)

            elif content == '!restart @' + self.nickname:
                self.send_chat('/me is now restarting.', reply)
                self.quit()

            elif (content == '!kill @' + self.nickname):
                if host:
                    self.send_chat('/me is now exiting. RIP in peace.', reply)
                    self.isAlive = False
                    self.quit()
                else:
                    self.send_chat('Error: "!kill" is a host-only command.', reply)

            else:
                super().handle_message(data)