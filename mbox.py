#! /usr/bin/env python3
# ~*~ utf-8 ~*~
# Taken from https://gist.github.com/benwattsjones/060ad83efd2b3afc8b229d41f9b246c4

import mailbox
import bs4
import os.path as op
from email.header import decode_header
import os, time
from datetime import datetime

DIR = '/mnt/btrfs/restore/tmp/mbox/Takeout/Post/'


def get_html_text(html):
    try:
        return bs4.BeautifulSoup(html, 'lxml').body.get_text(' ', strip=True)
    except AttributeError:  # message contents empty
        return None

timeformat = '%a, %d %b %Y %H:%M:%S %z'
timeformatGMT = '%a, %d %b %Y %H:%M:%S %z (%Z)'

def isTimeFormat(input, format):
    try:
        datetime.strptime(input, format)
        return True
    except ValueError:
        return None

# Some funcitons to convert time to a datetime element
def createDateTime(timeString):
    # dt = datetime.fromisoformat(timeString)
    if isTimeFormat(timeString, timeformat):
        dt = datetime.strptime(timeString, timeformat)
        return dt
    elif isTimeFormat(timeString, timeformatGMT):
        dt = datetime.strptime(timeString, timeformatGMT)
        return dt
    else:
        return None
        # timeString1 = timeString.split(' (')[0]
        # print(timeString, timeString1)
        # if timeString == timeString1:
        #     # raise ValueError('cannot convert {} '.format(timeString))
        #     print('cannot convert {} '.format(timeString))
        #     return None
        # if isTimeFormat(timeString, timeformat):
        #     dt = datetime.strptime(timeString, timeformat)
        #     return dt

class GmailMboxMessage():

    def __init__(self, email_data):
        if not isinstance(email_data, mailbox.mboxMessage):
            raise TypeError('Variable must be type mailbox.mboxMessage')
        self.email_data = email_data

    def parse_email(self):
        email_labels = self.email_data['X-Gmail-Labels']
        email_date = self.email_data['Date']
        email_from = self.email_data['From']
        email_to = self.email_data['To']
        email_subject = self.email_data['Subject']
        email_text = self.read_email_payload()

    def read_email_payload(self):
        email_payload = self.email_data.get_payload()
        if self.email_data.is_multipart():
            email_messages = list(self._get_email_messages(email_payload))
        else:
            email_messages = [email_payload]
        return [self._read_email_text(msg) for msg in email_messages]

    def attachments(self):
        if self.email_data.get_content_maintype() == 'multipart':
            for part in self.email_data.walk():
                if part.get_content_maintype() == 'multipart': continue
                if part.get('Content-Disposition') is None: continue
                filename = part.get_filename()

                if filename is None:
                    continue

                dec_obj = decode_header(filename)
                s, enc = dec_obj[0]

                if enc is None:
                    filename = s
                else:
                    filename = s.decode(enc, errors='ignore')

                # print(filename)
                base, ext = op.splitext(filename)
                filename = base[:70] + ext
                filename = filename.replace("/", "-")
                pathname = op.join(DIR, 'files', filename)
                print(pathname, end='')
                if op.exists(pathname):
                    print(" exists ")
                else:
                    content = part.get_payload(decode=True)
                    if content:
                        fb = open(pathname, 'wb')
                        fb.write(content)
                        fb.close()
                        print(' saved')
                    else:
                        print(' has no content')
                # set date to message date

                # d = self.email_data['date']
                # try:
                #     dt = createDateTime(d)
                #     print(time.mktime(dt.timetuple()))
                # except ValueError:
                #     pass


    def _get_email_messages(self, email_payload):
        for msg in email_payload:
            if isinstance(msg, (list, tuple)):
                for submsg in self._get_email_messages(msg):
                    yield submsg
            elif msg.is_multipart():
                for submsg in self._get_email_messages(msg.get_payload()):
                    yield submsg
            else:
                yield msg

    def _read_email_text(self, msg):
        content_type = 'NA' if isinstance(msg, str) else msg.get_content_type()
        encoding = 'NA' if isinstance(msg, str) else msg.get(
            'Content-Transfer-Encoding', 'NA')
        if 'text/plain' in content_type and 'base64' not in encoding:
            msg_text = msg.get_payload()
        elif 'text/html' in content_type and 'base64' not in encoding:
            msg_text = get_html_text(msg.get_payload())
        elif content_type == 'NA':
            msg_text = get_html_text(msg)
        else:
            msg_text = None
        return (content_type, encoding, msg_text)


######################### End of library, example of use below

mbox_obj = mailbox.mbox(op.join(DIR, 'mbox1.mbox'))

for key in mbox_obj.iterkeys():
    print(key)

# num_entries = len(mbox_obj)

print(datetime.now())

for idx, email_obj in enumerate(mbox_obj):
    email_data = GmailMboxMessage(email_obj)
    email_data.parse_email()
    print('Parsing email {0}'.format(idx))
    # print(email_data.read_email_payload())
    print(email_data.attachments())
