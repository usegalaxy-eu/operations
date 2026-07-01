#!/usr/bin/env python3
#
# Name:	smtpsend.py
# Athr:	janky
# Desc:	Extremely simple, mostly mail[x]-compatible SMTP null-client
# Vrsn: 3.4.2 2026-06-03

import os
import sys
import ssl
import socket
import smtplib

from optparse import OptionParser
from datetime import datetime
from datetime import timezone

#
# Configuration options, change these to match your site's mail server setup;
# values specified here have higher precedence than any autodetected ones,
# but can be overridden by command line options. Specify None to rely on auto
# detection (if available).
#
default_smtp_host = 'smtp.informatik.uni-freiburg.de'

default_sender = None


def standalone():
    """Return True if running standalone (i.e. not as a module)."""
    return __name__ == '__main__'


def eprint(msg):
    print(msg, file=sys.stderr)

def give_up(exit_code):
    eprint('Exiting')
    sys.exit(exit_code)


def fmt_error(msg, info):
    """Format an error message with associated error information."""
    # currently just a stub...
    return '%s: %s' % (msg, str(info))


def fmt_smtp_error(msg, info):
    """Format an smtplib error message."""
    # currently just a stub...
    if hasattr(info, 'smtp_code') and hasattr(info, 'smtp_error'):
        return '%s: [code=%d] %s'%(msg,info.smtp_code,info.smtp_error.decode())
    else:
        return '%s: %s' % (msg, str(info))


def fmt_rcpt_rej(rinfo):
    """Format an error message for rejected recipients."""
    mfmt = 'Recipient "%s" rejected: [code=%d] %s'
    msgs = [mfmt % (rcpt, rslt[0], rslt[1].decode())
            for (rcpt, rslt) in rinfo.items()]
    return '\n'.join(msgs)


def datetime_string():
    """Return a datetime string w/ current TZ info."""
    fmt = '%a, %d %b %Y %H:%M:%S %z (%Z)'
    now = datetime.now(tz=timezone.utc).astimezone()
    return now.strftime(fmt)


def subject_header(subject):
    """Construct the Subject:-header."""
    return 'Subject: %s\n' % (subject)


def reply_to_header(reply_to):
    """Construct the Reply-To:-header."""
    return 'Reply-To: %s\n' % (reply_to)


def minimal_headers(hdrfrom, rcpt_list, stime=datetime_string()):
    """Construct the minimum SMTP headers: From:, To:, Date:"""
    hdr_format = 'From: %s\nTo: %s\nDate: %s\n'
    to_list = ',\n    '.join(rcpt_list)
    return hdr_format % (hdrfrom, to_list, stime)


def send_smtp(options, to_list, body, subject='', verbosity=0):
    """Send the message in BODY to all recipients in TO_LIST.
       SUBJECT, defaults to '' and can be overriden if needed.
       This procedure calls send_822() q.v."""
    
    msg = subject_header(subject) + '\n' + body
    if options.reply_to != None:
        msg = reply_to_header(options.reply_to) + msg
    return send_822(options, to_list, msg, verbosity)


def send_822(options, to_list, msg, verbosity=0):
    """Take an almost complete RFC-822 message contained in MSG and
       send it to the recipients in TO_LIST (thereby completing
       the message by prepending 'From:'. 'To:'- and 'Date:'-headers.

       Return value: (return_code, refused_count, error_message)

       return_code == 0 indicates success
       return_code >= 1 indicates at least one rcpt was refused
       return_code >= 2 indicates serious problems
       return_code >= 8 indicates delivery failed completely
       refused_count is only meaningful for return_code <= 1

       This function is actually mis-named as the SMTP protocol
       was first defined in RFC-821 (RFC-822 defined the address
       format)."""
    return_code = 0
    refused_count = 0
    error_message = ''
    fromaddr = options.sender
    server_host = options.smtp_host
    server = smtplib.SMTP(server_host)

    # force a string value for TO_LIST to a list of len 1
    if isinstance(to_list, str):
        to_list = [to_list]

    try:
        server.set_debuglevel(verbosity)
        server.connect(server_host)
        message = minimal_headers(fromaddr, to_list) + msg
        if options.uname:
            ssl_context = ssl.create_default_context()
            ssl_context.verify_mode = ssl.CERT_OPTIONAL
            ssl_context.check_hostname = False
            server.starttls(context=ssl_context)
            server.login(options.uname, options.upass)
        status = server.sendmail(fromaddr, to_list, message)
        error_message = fmt_rcpt_rej(status)
        if len(status) > 0:
            return_code = 1
            refused_count = len(status)
    except smtplib.SMTPRecipientsRefused as e:
        # this exception is raised iff *all* recipients were rejected
        error_message = fmt_rcpt_rej(e.recipients)
        refused_count = len(e.recipients)
        return_code = 8
    except smtplib.SMTPResponseException as e:
        # other SMTP response errors are handled here
        error_message = fmt_smtp_error('SMTP error', e)
        if e.smtp_code >= 400:
            return_code = 4
        if e.smtp_code >= 500:
            return_code = 8
    except smtplib.SMTPException as e:
        # give up on all other smtplib exceptions
        error_message = fmt_smtp_error('SMTP exception', e)
        return_code = 8
    except socket.error as e:
        # connection errors are not caught by smtplib proper
        error_message = fmt_smtp_error('Connection to SMTP server failed', e)
        return_code = 8
    except:
        eprint('ERROR: Unexpected exception in smtplib:')
        raise
    finally:
        try: server.quit()
        except: pass

    return (return_code, refused_count, error_message)


def autodetect_sender():
    """Autodetect a reasonable default value for the sender;
       currently name service lookups are avoided."""
    username = os.getlogin()
    hostname = socket.gethostname().split('.', 1)
    if len(hostname) == 2:
        return username + '@' + hostname[1]
    else:
        return username


def option_parser():
    """Return a parser for this program's cmdline args"""
    usage = 'usage: smtpsend [options] recipient [...]'
    parser = OptionParser(usage=usage)
    parser.add_option('-R', help='reply-to address',
                      dest='reply_to', default=None)
    parser.add_option('-s', help='message subject',
                      dest='subject', default='')
    parser.add_option('-S', help='SMTP server host',
                      dest='smtp_host', default=default_smtp_host)
    parser.add_option('-T', help='input is RFC-822 template',
                      dest='template', default=False, action='store_true')
    parser.add_option('-u', help='sender address',
                      dest='sender', default=default_sender)
    parser.add_option('-U', help='login username',
                      dest='uname', default=None)
    parser.add_option('-P', help='login password',
                      dest='upass', default='')
    parser.add_option('-v', help='verbose mode, show details of delivery',
                      dest='verbose', default=False, action='store_true')
    return parser


def option_autodetect(opts):
    """Set defaults for required values not provided on the command line;
       return the updated value of OPTS."""
    # get the base data from the OS, avoid name service lookups
    # fill in opts.sender
    if opts.sender == None:
        opts.sender = autodetect_sender()
    return opts


def main():
    """Main entry point."""
    vlevel = 0
    parser = option_parser()
    (options, args) = parser.parse_args()
    options = option_autodetect(options)
    #print('DBG: options = %s' % repr(options)) # DBG
    if args == []:
        eprint('No recipients specified, nothing to do, exiting.')
        sys.exit(0)
    else:
        if options.template and options.subject != '':
            eprint("The '-s' and '-T' options are mutually exclusive")
            sys.exit(2)
        if options.verbose: vlevel = 1

        message_body = sys.stdin.read()
        recipients = args
        if options.template:
            (rcode, refused, errmsg) = send_822(options,
                                                 recipients,
                                                 message_body,
                                                 verbosity=vlevel)
        else:
            message_subject = options.subject
            (rcode, refused, errmsg) = send_smtp(options,
                                                 recipients,
                                                 message_body,
                                                 message_subject,
                                                 verbosity=vlevel)
        if rcode != 0 and errmsg != '':
            eprint(errmsg)
        sys.exit(rcode)

if standalone(): main()

# EOF: smtpsend.py
