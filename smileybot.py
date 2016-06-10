import euphoria
import contextlib
import urllib.parse, urllib.error, urllib.request
import random
import json
import time, datetime
import imgurpython, imgurpython.helpers.error
import logging

logging.basicConfig(level=logging.DEBUG, filename='smileybot.log')

with open('client') as clientinfo:
    client_id = clientinfo.readline().rstrip('\n')
    client_secret = clientinfo.readline().rstrip('\n')

client = imgurpython.ImgurClient(client_id, client_secret)


class SmileBot(euphoria.ping_room.PingRoom, euphoria.standard_room.StandardRoom):
    def __init__(self, room, passcode=None):
        super().__init__(room, passcode)
        self.nickname = 'SmileBot'

        self.times = []
        self.log = 5
        self.cooldown = 30

        self.parent = None

        self.open_list()

        self.ping_text = 'Pong!'
        self.short_help_text = 'Bot for creating custom "smiley" image macros.'
        self.help_text = (self.nickname + '(formerly Smileys) is a bot created by @SillyLyn in Python using EuPy '
                          '(https://github.com/jedevc/EuPy)\n\nUse the following command to add new smileys:\n!add '
                          '<name> <image>\nImages must be DIRECT LINKS to Imgur images.\n\nThe following commands '
                          'are also available:\n!list @' + self.nickname + '\n!top @' + self.nickname + '\n!info <name>'
                          '\n!me_irl\n!random\n\nSpecial thanks to @Alexis for being awesome <3')

    def handle_chat(self, m):
        self.parent = m['id']

        message = euphoria.command.Command(m['content'])
        message.parse()

        # command: "!add <key> <URL>"
        if message.command == 'add':
            if not len(message.args) == 2:
                self.send_chat('~bad syntax puppies~ https://i.imgur.com/ieajOG4.jpg', m['id'])
                self.send_chat('Error: Bad syntax.\nUsage: !add <name> <URL>', m['id'])
            else:
                self.add_smiley(message.args[0].casefold(), message.args[1], m['sender']['name'], parent=m['id'])

        # host command: "!remove <key>"
        elif message.command == 'remove':
            host = m['sender'].get('is_manager', False)
            if host:
                if not len(message.args) == 1:
                    self.send_chat('Error: Bad syntax.\nUsage: !remove <name>', m['id'])
                else:
                    self.remove_smiley(message.args[0].casefold(), m['id'])
            else:
                self.send_chat('Error: "!remove" is a host-only command.', m['id'])

        # command: "!info --option <arg>
        elif message.command == 'info' and len(message.flags) == 1:
            self.send_info(' '.join(message.args), m['id'], option=list(message.flags)[0][1:])

        # command: "!me_irl"
        elif (m['content'] == '!me_irl') or (m['content'] == '!meirl'):
            self.me_irl(m['sender']['name'], m['id'])

        # command: "!random"
        elif m['content'] == '!random':
            self.random_smiley(m['id'])

        else:
            self.send_smiley(m['content'], m['id'])

    def open_list(self):
        with open('list.json', 'r') as imagelist:
            self.list = json.load(imagelist)

    def write_list(self):
        with open('list.json', 'w') as imagelist:
            json.dump(self.list, imagelist)

    def limit(self, parent):
        while len(self.times) > self.log:
            del self.times[0]
        if len(self.times) == self.log and time.time() - self.times[0] < self.cooldown:
            self.send_chat('Error: Cooldown limit reached. Please wait about ' +
                           str(round((self.cooldown - (time.time() - self.times[0]))/60, 1)) +
                           ' minutes, then try again.', parent)
            return False
        else:
            return True

    def record_data(self, key):
        self.times.append(time.time())
        self.list[key]['count'] = str(int(self.list[key]['count']) + 1)
        self.write_list()

    def send_smiley(self, key, parent=None):
        if key in self.list and self.limit(parent):
            self.send_chat(self.list[key].get('imgur_url', self.list[key]['url']).rstrip('?1'), parent)
            self.record_data(key)

    def send_list(self, parent=None):
        msg = ''
        for key in self.list:
            msg = msg + key + ', '
        self.send_chat('List of available smileys:\n' + msg[:-2], parent)

    def send_info(self, key, parent=None, option=None):
        if option == 'image':
            if ' ' in key:
                return
            if key.startswith('"') or key.startswith('<'):
                key = key[1:-1]
            if not key[0] == '!':
                key = '!' + key
            key = key.casefold()
            with contextlib.suppress(KeyError):
                self.send_chat('Info for smiley "' + key + '":\nOriginal URL: "' + self.list[key].get('url', '') +
                               '"\nImgur URL: "' + self.list[key].get('imgur_url', '') + '"\nUsage count: ' +
                               self.list[key]['count'] + '\nAdded by: ' + self.list[key].get('user','') +
                               '\nTime added (UTC): ' + self.list[key].get('date',''), parent)

        if option == 'user':
            count = 0
            for image in self.list:
                if self.list[image].get('user', None) == key:
                    count += 1
            self.send_chat('User ' + key + ' has added ' + str(count) + ' images.', parent)

        if option == 'list' and key.casefold() == '@' + self.nickname.casefold():
            self.send_list(parent)

        if option == 'top' and key.casefold() == '@' + self.nickname.casefold():
            self.top_smileys(parent)

    def imgur_verification(self, url, parent=None):

        if not 'imgur.com' in urllib.parse.urlparse(url).netloc:
            return False

        # Check url is accessible
        try:
            client.get_image(urllib.parse.urlparse(url).path.split('.')[0][1:])
        except imgurpython.helpers.error.ImgurClientError:
            self.send_chat('Error: Invalid URL. Please check that the URL is correct.', parent)
            return False
        else:
            return True

    def non_imgur_verification(self, url, parent=None):
        try:
            valid_link = urllib.request.urlopen(url).info().get_content_type().startswith('image')
        except urllib.error.HTTPError:
            self.send_chat('Error: Bad link. Please make sure you are using a valid link and try again.', parent)
            return False
        except urllib.error.URLError:
            self.send_chat('Error: Invalid URL. Please check that the URL is correct.', parent)
            return False
        else:
            if valid_link:
                return True
            else:
                self.send_chat(('Error: Link provided is not an image. Please make sure you are using a valid link and '
                                'try again.'), parent)
                return False

    def add_smiley(self, key, url, user, parent=None):
        if key.startswith('"') or key.startswith('<'):
            key = key[1:-1]
        if not key[0] == '!':
            key = '!' + key

        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url

        #  verify some error conditions and reply to user
        if key in self.list:
            self.send_chat('Error: Name already in use. Please choose a different name.', parent)
            return
        if key in ('!', '!list', '!add', '!help', '!ping', '!uptime', '!pause', '!restore', '!restart', '!kill',
                   '!comic', '!remove', '!me_irl', '!meirl', '!discussion', '!conversation', '!random', '!info',
                   '!top'):
            self.send_chat('Error: Name prohibited. Please choose a different name.', parent)
            return
        for character in key[1:]:
            if not (character.isalnum() or character == '_'):
                self.send_chat(('Error: Numbers and special characters may not be used in names. Please choose a '
                                'different name.'), parent)
                return

        if self.imgur_verification(url, parent):
            self.list[key] = {'url': url, 'imgur_url': url, 'count': '0', 'user': user,
                              'date': str(datetime.datetime.utcnow()), 'deletehash': None}
            self.write_list()
            self.send_chat('New smiley "' + key + '" added.', parent)
        elif self.non_imgur_verification(url, parent):
            if client.get_credits()['UserRemaining'] >= 10:
                try:
                    img = client.upload_from_url(url)
                    self.list[key] = {'url': url, 'imgur_url': img['link'], 'count': '0', 'user': user,
                                      'date': str(datetime.datetime.utcnow()), 'deletehash': None}
                    self.write_list()
                    self.send_chat('New smiley "' + key + '" added.', parent)
                except imgurpython.helpers.error.ImgurClientRateLimitError:
                    self.send_chat('Error: Imgur Rate Limit Error. Unable to add smiley.', parent)
            else:
                self.send_chat('Not enough Imgur credits. Please reupload the image to Imgur yourself or try again '
                               'tomorrow.', parent)

    def remove_smiley(self, key, parent=None):
        if key.startswith('"') or key.startswith('<'):
            key = key[1:-1]
        if not key[0] == '!':
            key = '!' + key
        if self.list[key].get('deletehash', False):
            if client.delete_image(self.list[key]['deletehash']):
                self.send_chat('Imgur image successfully deleted.', parent)
            else:
                self.send_chat('Error: Unable to delete Imgur image. Smiley data will not be removed.', parent)
                return
        try:
            del self.list[key]
        except KeyError:
            self.send_chat('Error: Smiley name not in list. Please check that the name is correct.', parent)
        else:
            self.write_list()
            self.send_chat('Smiley "' + key + '" removed.', parent)

    def me_irl(self, sender, parent=None):
        if self.limit(parent):
            if sender.count(':') == 2 and sender[0] == ':' and sender[-1] == ':':
                sender = sender[1:-1]
            while (not sender.count(':') == 0) and sender.count(':') % 2 == 0:
                sender = sender.partition(':')[0] + sender.partition(':')[2].partition(':')[2]

            key = '!'
            for character in sender:
                if character.isalnum() or character == '_':
                    key = key + character

            with contextlib.suppress(KeyError):
                self.send_chat(self.list[key.casefold()]['url'], parent)
                self.record_data(key.casefold())

    def random_smiley(self, parent):
        if self.limit(parent):
            r = random.randint(0, len(list(self.list))-1)
            self.send_chat(list(self.list)[r] + self.list[list(self.list)[r]]['url'], parent)
            self.record_data(list(self.list)[r])

    def top_smileys(self, parent):
        top = []
        for key in self.list:
            top.append((int(self.list[key]['count']), key))
        top.sort()
        message = 'Top 10 Smileys:'
        for number in range(1,11):
            message = message + '\n' + str(number) + '. ' + top[-number][1] + ' (' + str(top[-number][0]) + ')'
        self.send_chat(message, parent)


def main(room='test'):
    bot = SmileBot(room)
    while bot.isAlive:
        try:
            euphoria.executable.start(bot)
        except:
            logging.exception('')
            bot.send_chat('An unknown error occurred.', bot.parent)


if __name__ == '__main__':
    main()
