#!/usr/bin/env python3
#
# Name: mimeenc.py
# Athr: janky
# Desc: quick & dirty MIME encoder (can be used with 'smtpsend -T')
# Vrsn: 1.0 2021-02-19

import io
import sys

from email import charset
from email.header import Header
from email.mime.text import MIMEText


def mime_encode(msgtext):
    """MIME-Encode the (partial) e-mail message in msgtext.

    Return an instance of email.mime.text.MIMEText.

    The input string must contain at least one header line,
    usually the Subject:-line, followed by an empty line
    and the message body. To:, From: and Date: are not allowed,
    as these will be added when the message is sent.
    """
    allowed = ['subject', 'reply-to', 'cc']

    def collect_hdrs(f, hlst=[]):
        for line in f:
            if line.strip() == '':
                return hlst
            try:
                (name, value) = line.split(':')
                hlst.append((name.capitalize(), value.strip()))
            except ValueError:
                return []

    def check_hdrs(hlst):
        if hlst == []:
            return False
        for (name, value) in hlst:
            if name.lower() not in allowed:
                return False
        return True

    msgf = io.StringIO(msgtext)
    hlst = collect_hdrs(msgf)
    if not check_hdrs(hlst):
        return False

    mtxt = MIMEText(msgf.read())
    for (name, value) in hlst:
        mtxt[name] = Header(value)

    return mtxt


def get_raw_msg_text(fname):
    """Return the contents of fname."""
    try:
        with open(fname, 'rt', encoding='utf-8') as f:
            return f.read()
    except OSError as e:
        fatal_os_error(e)


def fatal_os_error(e, ecode=2):
    """Write OS error message for expn e to stderr and exit with ecode."""
    fmt = 'OS Error[%d]: %s - %s'
    fatal(fmt, (e.errno, e.filename, e.strerror), ecode)


def main():
    # make email.mime-classes use quoted-printable as encoding
    # this setting will be needed later
    charset.add_charset('utf-8', charset.SHORTEST, charset.QP)

    raw_msg = get_raw_msg_text(sys.argv[1])
    mime_msg = mime_encode(raw_msg)
    print(mime_msg)


if __name__ == '__main__': main()

# EOF: mimeenc.py
