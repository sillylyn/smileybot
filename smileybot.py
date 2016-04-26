import euphoria
import contextlib
import urllib.error, urllib.request
import random
import json
import time, datetime

class SmileBot(euphoria.ping_room.PingRoom, euphoria.standard_room.StandardRoom):
    def __init__(self, room, passcode=None):
        super().__init__(room, passcode)
        self.nickname = 'SmileBot'

        self.times = []
        self.logging_max = 5
        self.cooldown = 120

        self.open_list()


        self.ping_text = 'Pong!'
        self.short_help_text = 'Bot for creating custom "smiley" image macros.'
        self.help_text = ('SmileBot (formerly Smileys) is a bot created by @SillyLyn in Python using EuPy '
                          '(https://github.com/jedevc/EuPy)\n\nUse the following command to add new smileys:\n!add '
                          '<name> <image>\nImages must be DIRECT LINKS to Imgur images.\n\nFor a list of available '
                          'smileys, use the following command:\n!list @Smileys\n\nSpecial thanks to @blahdom for being '
                          'awesome <3')

    def handle_chat(self, m):
        if m['content'].startswith('!add '):
            try:
                cmd, key, url = m['content'].split()
            except ValueError:
                self.send_chat('~bad syntax puppies~ https://i.imgur.com/ieajOG4.jpg', m['id'])
                self.send_chat('Error: Bad syntax.\nUsage: !add <name> <URL>', m['id'])
            else:
                self.add_smiley(key.casefold(), url, m['sender']['name'], parent=m['id'])
        elif m['content'].startswith('!remove '):
            host = m['sender'].get('is_manager', False)
            if host:
                try:
                    cmd, name = m['content'].split()
                except ValueError:
                    self.send_chat('Error: Bad syntax.\nUsage: !remove <name>', m['id'])
                else:
                    self.remove_smiley(name, m['id'])
            else:
                self.send_chat('Error: "!remove" is a host-only command.', m['id'])
        elif m['content'] == '!list @' + self.nickname:
            self.send_list(m['id'])
        elif m['content'].startswith('!info '):
            try:
                cmd, name = m['content'].split()
            except ValueError:
                self.send_chat('Error: Bad syntax.\nUsage: !info <name>', m['id'])
            else:
                self.send_info(name, m['id'])
        elif m['content'] == '!top @' + self.nickname:
            self.top_smileys(m['id'])
        elif (m['content'] == '!me_irl') or (m['content'] == '!meirl'):
            self.me_irl(m['sender']['name'], m['id'])
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

    def send_smiley(self, key, parent=None):
        while len(self.times) > self.logging_max:
            del self.times[0]
        if key in self.list and len(self.times) == self.logging_max and time.time() - self.times[0] < self.cooldown:
            self.send_chat('Error: Cooldown limit reached. Please wait about ' +
                           str(round((self.cooldown - (time.time() - self.times[0]))/60, 1)) +
                           ' minutes, then try again.', parent)
        else:
            with contextlib.suppress(KeyError):
                self.send_chat(self.list[key]['url'], parent)
                self.times.append(time.time())
                self.list[key]['count'] = str(int(self.list[key]['count']) + 1)
                self.write_list()

    def send_list(self, parent=None):
        msg = ''
        for key in self.list:
            msg = msg + key + ', '
        self.send_chat('List of available smileys:\n' + msg[:-2], parent)

    def send_info(self, key, parent=None):
        if key.startswith('"') or key.startswith('<'):
            key = key[1:-1]
        if not key[0] == '!':
            key = '!' + key
        try:
            self.send_chat('Info for smiley "' + key + '":\nImgur URL: "' + self.list[key]['url'] + '"\nUsage count: ' +
                           self.list[key]['count'] + '\nAdded by: ' + self.list[key].get('user','') +
                           '\nTime added (UTC): ' + self.list[key].get('date',''), parent)
        except KeyError:
            self.send_chat('Error: Error: Smiley name not in list. Please check that the name is correct.', parent)

    def add_smiley(self, key, filename, user, parent=None):
        if key.startswith('"') or key.startswith('<'):
            key = key[1:-1]
        if not key[0] == '!':
            key = '!' + key
        #  verify some error conditions and reply to user
        if key in self.list:
            self.send_chat('Error: Name already in use. Please choose a different name.', parent)
            return
        if 'i.imgur.com' not in filename:
            self.send_chat('Error: Only direct links to i.imgur.com are permitted.', parent)
            return
        if key in ('!', '!list', '!add', '!help', '!ping', '!uptime', '!pause', '!restore', '!restart', '!kill',
                   '!comic', '!remove', '!me_irl', '!meirl', '!discussion', '!conversation', '!random', '!info',
                   '!top'):
            self.send_chat('Error: Name prohibited. Please choose a different name.', parent)
            return
        if not key[1:].isalnum():
            self.send_chat(('Error: Numbers and special characters may not be used in names. Please choose a '
                            'different name.'), parent)
            return

        # sanitize the filename if necessary
        if filename.startswith('"') or filename.startswith("<"):
            filename = filename[1:-1]
        if not filename.startswith('http://') and not filename.startswith('https://'):
            filename = 'http://' + filename
        if filename.endswith('?1'):
            filename = filename[:-2]

        # Check url is accessible
        try:
            valid_link = urllib.request.urlopen(filename).info().get_content_type().startswith('image')
        except urllib.error.HTTPError:
            self.send_chat(('Error: Bad link. Please make sure you are using a valid i.imgur.com direct link '
                            'and try again.'), parent)
        except urllib.error.URLError:
            self.send_chat('Error: Invalid URL. Please check that the URL is correct.', parent)
        else:
            if valid_link:
                self.list[key] = {'url':filename, 'count': '0', 'user': user, 'date': str(datetime.datetime.utcnow())}
                self.write_list()
                self.send_chat('New smiley "' + key + '" added.', parent)
            else:
                self.send_chat(('Error: Link provided is not an image. Please make sure you are using'
                                'a valid i.imgur.com direct link and try again.'), parent)

    def remove_smiley(self, key, parent=None):
        if key.startswith('"') or key.startswith('<'):
            key = key[1:-1]
        if not key[0] == '!':
            key = '!' + key
        try:
            del self.list[key]
        except KeyError:
            self.send_chat('Error: Smiley name not in list. Please check that the name is correct.', parent)
        else:
            self.write_list()
            self.send_chat('Smiley "' + key + '" removed.', parent)

    def me_irl(self, sender, parent=None):
        while len(self.times) > self.logging_max:
            del self.times[0]
        if len(self.times) == self.logging_max and time.time() - self.times[0] < self.cooldown:
            self.send_chat('Error: Cooldown limit reached. Please wait about ' +
                           str(round((self.cooldown - (time.time() - self.times[0]))/60, 1)) +
                           ' minutes, then try again.', parent)
        else:
            name = sender.split(':')
            for string in name:
                with contextlib.suppress(KeyError):
                    key = '!' + ''.join(string.casefold().split())
                    self.send_chat(self.list[key]['url'], parent)
                    self.list[key]['count'] = str(int(self.list[key]['count']) + 1)
                    self.write_list()
                    break

    def random_smiley(self, parent):
        while len(self.times) > self.logging_max:
            del self.times[0]
        if len(self.times) == self.logging_max and time.time() - self.times[0] < self.cooldown:
            self.send_chat('Error: Cooldown limit reached. Please wait about ' +
                           str(round((self.cooldown - (time.time() - self.times[0]))/60, 1)) +
                           ' minutes, then try again.', parent)
        else:
            r = random.randint(0, len(list(self.list))-1)
            self.send_chat(self.list[list(self.list)[r]]['url'], parent)
            self.list[list(self.list)[r]]['count'] = str(int(self.list[list(self.list)[r]]['count']) + 1)
            self.write_list()

    def top_smileys(self, parent):
        toplist = []
        for key in self.list:
            toplist.append((int(self.list[key]['count']), key))
        toplist.sort()
        message = 'Top 10 Smileys:'
        for number in range(1,11):
            message = message + '\n' + str(number) + '. ' + toplist[-number][1] + ' (' + str(toplist[-number][0]) + ')'
        self.send_chat(message, parent)
        print(toplist)


def main(room = 'srs'):
    bot = SmileBot(room)
    while bot.isAlive:
        euphoria.executable.start(bot)

if __name__ == '__main__':
    main()
