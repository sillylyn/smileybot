import euphoria
import contextlib
import urllib.error
import urllib.request


class SmileyBot(euphoria.ping_room.PingRoom, euphoria.standard_room.StandardRoom):
    def __init__(self, room, passcode=None):
        super().__init__(room, passcode)
        self.nickname = 'Smileys'
        self.list = {}
        self.open_list()

        self.ping_text = 'Pong!'
        self.short_help_text = 'Bot for creating custom "smiley" image macros.'
        self.help_text = ('Smileys is a bot created by @SillyLyn in Python using EuPy (https://github.com/jedevc/EuPy)'
                          '\n\nUse the following command to add new smileys:\n!add <name> <image>\nImages must be '
                          'DIRECT LINKS to Imgur images.\n\nFor a list of available smileys, use the following command:'
                          '\n!list @Smileys\n\nSpecial thanks to @blahdom for being awesome <3')

    def handle_chat(self, m):
        if m['content'].startswith('!add'):
            try:
                cmd, name, url = m['content'].split(' ')
            except ValueError:
                self.send_chat('~bad syntax puppies~ https://i.imgur.com/ieajOG4.jpg')
                self.send_chat('Error: Bad syntax.\nUsage: !add <name> <URL>', m['id'])
            else:
                self.add_smiley(name.lower(), url, parent=m['id'])
        elif m['content'].startswith('!remove'):
            try:
                host = m['sender']['is_manager']
            try:
                cmd, name = m['content'].split(' ')
            except ValueError:
                self.send_chat('Error: Bad syntax.\nUsage: !remove <name>', m['id'])
            else:
                self.remove_smiley(name, m['id'])
        elif m['content'] == '!list @' + self.nickname:
            self.send_list(m['id'])
        else:
            with contextlib.suppress(KeyError):
                self.send_chat(self.list[m['content'].lower()], m['id'])

    def open_list(self):
        with open('list.txt', 'r') as smileylist:
            for line in smileylist:
                if len(line.split()) == 2:
                    self.list[line.split()[0]] = line.split()[1].rstrip('\n')

    def write_list(self):
        output = ''
        for key in self.list:
            output = output + key + ' ' + self.list[key] + '\n'
        with open('list.txt', 'w') as smileylist:
            smileylist.write(output)

    def send_list(self, parent=None):
        msg = ''
        for key in self.list:
            msg = msg + key + ', '
        self.send_chat('List of available smileys:\n' + msg[:-2], parent)

    def add_smiley(self, command, filename, parent=None):
        if not command[0] == '!':
            command = '!' + command
        #  verify some error conditions and reply to user
        if command in self.list:
            self.send_chat('Error: Name already in use. Please choose a different name.', parent)
            return
        if 'i.imgur.com' not in filename:
            self.send_chat('Error: Only direct links to i.imgur.com are permitted.', parent)
            return
        if command in ('!', '!list', '!add', '!help', '!ping', '!uptime', '!pause', '!restore', '!restart', '!kill'):
            self.send_chat('Error: Name prohibited. Please choose a different name.', parent)
            return
        if not command[1:].isalnum():
            self.send_chat(('Error: Numbers and special characters may not be used in names. Please choose a '
                            'different name.'), parent)
            return

        # sanitize the filename if necessary
        if filename.startswith('"') or filename.startswith("'"):
            filename = filename[1:-1]
        if not filename.startswith('http://') and not filename.startswith('https://'):
            filename = 'http://' + filename

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
                self.list[command] = filename
                with open('list.txt', 'a') as smileylist:
                    smileylist.write('\n' + command + ' ' + filename)
                self.send_chat('New smiley "' + command + '" added.', parent)
            else:
                self.send_chat(('Error: Link provided is not an image. Please make sure you are using'
                                'a valid i.imgur.com direct link and try again.'), parent)

    def remove_smiley(self, command, parent=None):
        if not command[0] == '!':
            command = '!' + command
        try:
            del self.list[command]
        except KeyError:
            self.send_chat('Error: Smiley name not in list. Please check that the name is correct.', parent)
        else:
            self.write_list()
            self.send_chat('Smiley "' + command + '" removed.', parent)


def main(room = 'srs'):
    bot = SmileyBot(room)
    while bot.isAlive:
        euphoria.executable.start(bot)


if __name__ == '__main__':
    main()
