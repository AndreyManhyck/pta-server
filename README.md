# Practical Exam
Please **fork** this repo and **develop your server** based on the protocol described in [pta.pdf][ptad] file (in portuguese). Before coding, I suggest you carefully read the document spec and understand the protocol. Experiment the protocol, using paper and pencil, drawing examples of protocol usage.

Please develop your server code in the directory [pta-server][ptas]. The user list that must be accepted by the protocol must be read from the [pta-server/users.txt][ptau] file. The files to be served by your server are in the [pta-server/files][ptaa] directory. Please don't change these files and directories.

Your server code will be evaluated through an automatic testing tool. This way, in order to test your code you can use the [pta-client.py][ptac] file. This file makes some tests but it is not an extensive test. So, keep in mind that the actual evaluation will test other aspects of your protocol implementation.

You could use **any programming language**. But you must provide instructions in order to successfully run your code. Describe all stuff about libraries, interpreters, versions and so on. After finishing development, you must share the link of your github repo in the evaluation environment ([sigaa.ufpa.br](http://sigaa.ufpa.br/)).

## Running the server

The server is written in Python and uses only the standard library, so there is nothing to install.

| Item | Details |
|---|---|
| Interpreter | CPython 3.8 or newer |
| Tested with | CPython 3.13.15 and 3.15.0, on Windows 11 Pro |
| Libraries | Standard library only: `os`, `socket`, `sys` and `threading` |
| External dependencies | None: no `pip install` and no compilation |
| Network | TCP port 11550 by default, on all interfaces |

Start the server:

```bash
cd pta-server
python pta-server.py
```

On systems where `python` does not point to Python 3, use `python3`. To use another port, pass it as an argument, for example `python pta-server.py 12000`. Press `Ctrl+C` to stop the server.

With the server running, test it from the repository root in another terminal:

```bash
python pta-client.py 127.0.0.1 11550 user1
```

The expected result is `Points: 6/6` followed by `TERM is OK!`. The client picks a random file for the test and crashes with `UnicodeDecodeError` when it picks the `.png`, because it tries to decode binary data as text. If that happens, run it again. The server sends the file bytes unchanged. The client also saves the downloaded file in the current directory, so you may prefer to run it from a temporary directory.

The server finds `users.txt` and `files/` from the location of its script, so it can be started from any directory.

## Implementation decisions

| Situation | Behavior |
|---|---|
| Multiple clients | One thread per connection |
| Binary files | Read and sent as bytes, with no conversion |
| Empty file | `N ARQ 0 `, keeping the space after the size |
| `PEGA a b` | Sends `a` and ignores the others, as stated in section 3.1 of the specification |
| `PEGA` with a name outside the listing, such as `../users.txt` | `NOK` |
| `LIST` or `TERM` with arguments | `NOK`, because they do not match the format |
| Non-numeric `SEQ_NUM` | `NOK`, echoing the first field received |
| Empty message | `0 NOK` |
| End of message | Accepts messages with no terminator, with `\n` or with `\r\n` |
| Atomicity | Each connection processes one request at a time, from start to finish |
| Client disconnects | Ends only the thread of that connection |

Because the protocol does not define a message terminator, each socket read without `\n` is treated as one complete message.

[ptas]: <https://github.com/glaucogoncalves/pta/tree/master/pta-server>
[ptau]: <https://github.com/glaucogoncalves/pta/tree/master/pta-server/users.txt>
[ptaa]: <https://github.com/glaucogoncalves/pta/tree/master/pta-server/files>
[ptac]: <https://github.com/glaucogoncalves/pta/tree/master/pta-client.py>
[ptad]: <https://github.com/glaucogoncalves/pta/tree/master/pta.pdf>