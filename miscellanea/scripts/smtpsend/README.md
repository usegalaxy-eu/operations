# smtpsend.py

A minimal SMTP null-client. The syntax borrows from that of `mailx(1)`
but does not implement all its options while adding quite a few of its
own. The `--help` option lists all options available.

In order to test mail delivery via our SMTP server, the script could
be run as:
```
smtpsend.py -v -u galaxy-no-reply@informatik.uni-freiburg.de -U $UNAME -P $UPASS -s "$SUBJECT" $RECIPENT
```

(You should, needless to say, ***not*** give the password directly after `-P`;
putting it in an envar and referencing the var on the cmdline makes the pw
briefly visible in the process list but that's kinda okayish when run on a
machine where only admins have shell access anyway, the same goes for using
`$()` to cat a file containing the pw. When asked rly nicely I might be arsed
to add an option to read the pw directly from an envar...)

`mimeenc.py` is a companion script that could be used with the `-T` option
of `smtpsend.py`.
