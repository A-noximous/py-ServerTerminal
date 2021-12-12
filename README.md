# py-ServerTerminal
A python script fixing some issues with dedicated Minecraft Server terminals, such as adding output coloring(for info, warn and errors), and adding a seperate input frame, so no more being annoyed by server logs splitting whatever youre typing in console.

This project is still in-dev, so any and all suggestions are welcome, contributions are too.

## DISCLAIMER:
This will only work on Linux, as urwid, one of the python modules used in this project, doesn't work on Windows

## Dependencies:
### [Python](https://www.python.org/)
### [Urwid](https://urwid.org/)
### [Pexpect](https://pexpect.readthedocs.io/en/stable/)

Python installation differs based on your Linux distribution.
Both Urwid and Pexpect can be installed by running `pip3 install requirements.txt`.

## Running
Download both `terminal.py` and `reqrequirements.txt`, then: <br />
To run the server(the first time using the script), simply run `python3 terminal.py <your server start command>` in the directory where you have the `terminal.py` file
After that, you can just run `python 3 terminal.py` and your server will start, your command is stored in the `terminal.conf` file.
Your server start command should be something like `java -Xmx10G -jar ... server.jar`

You can both start and stop the server from within the script. To stop it you can run the Minecraft Server's `stop` command, and to start it up you can run `start` in the terminal script.

To quit out from the terminal, you can use `quit` or `exit`. This sends the `stop` command to the server before quiting out of the script.
`fquit` and `fexit` instantly stop the script(**NOT RECCOMENDED**)
`cls` and `clear` clear the terminal output(they are still saved in the server's log files).
