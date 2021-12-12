import urwid, threading, time, pexpect, os, sys
from collections import deque
from threading import *

class FocusMixin(object):
    def mouse_event(self, size, event, button, x, y, focus):
        if focus and hasattr(self, '_got_focus') and self._got_focus:
            self._got_focus()
        return super(FocusMixin,self).mouse_event(size, event, button, x, y, focus)

class ListView(FocusMixin, urwid.ListBox):
    def __init__(self, model, got_focus, max_size=None):
        urwid.ListBox.__init__(self,model)
        self._got_focus=got_focus
        self.max_size=max_size
        self._lock=threading.Lock()

    def add(self,line):
        with self._lock:
            was_on_end=self.get_focus()[1] == len(self.body)-1
            if self.max_size and len(self.body)>self.max_size:
                del self.body[0]
            self.body.append(urwid.Text(line))
            last=len(self.body)-1
            if was_on_end:
                self.set_focus(last,'above')

    def clear(self):
        with self._lock:
            was_on_end=self.get_focus()[1] == len(self.body)-1
            for i in range(64):
                self.body.append(urwid.Text(''))
            last=len(self.body)-1
            if was_on_end:
                self.set_focus(last,'below')

class Input(FocusMixin, urwid.Edit):
    signals=['line_entered']
    def __init__(self, got_focus=None):
        urwid.Edit.__init__(self)
        self.history=deque(maxlen=1000)
        self._history_index=-1
        self._got_focus=got_focus

    def keypress(self, size, key):
        if key=='enter':
            line=self.edit_text.strip()
            if line:
                urwid.emit_signal(self,'line_entered', line)
                self.history.append(line)
            self._history_index=len(self.history)
            self.edit_text=u''
        if key=='up':

            self._history_index-=1
            if self._history_index< 0:
                self._history_index= 0
            else:
                self.edit_text=self.history[self._history_index]
        if key=='down':
            self._history_index+=1
            if self._history_index>=len(self.history):
                self._history_index=len(self.history)
                self.edit_text=u''
            else:
                self.edit_text=self.history[self._history_index]
        else:
            urwid.Edit.keypress(self, size, key)

class Console(urwid.Frame):
    """
        Simple terminal UI with command input on bottom line and display frame.
    """

    class Exit(object):
        pass

    PALLETE=[('reversed', urwid.BLACK, urwid.LIGHT_GRAY),
              ('normal', urwid.LIGHT_GRAY, urwid.BLACK),
              ('ERROR', urwid.LIGHT_RED, urwid.BLACK),
              ('CLIENT', urwid.DARK_GREEN, urwid.BLACK),
              ('INFO', urwid.LIGHT_BLUE, urwid.BLACK),
              ('WARN', urwid.YELLOW, urwid.BLACK), ]

    def __init__(self, title="Title", command_caption='(Tab to switch focus to upper frame, where you can scroll text)', max_size=1000):
        self.header=urwid.Text(title)
        self.model=urwid.SimpleListWalker([])
        self.body=ListView(self.model, lambda: self._update_focus(False), max_size=max_size )
        self.input=Input(lambda: self._update_focus(True))
        foot=urwid.Pile([urwid.AttrMap(urwid.Text(command_caption), 'reversed'),
                        urwid.AttrMap(self.input,'normal')])
        urwid.Frame.__init__(self,
                             urwid.AttrWrap(self.body, 'normal'),
                             urwid.AttrWrap(self.header, 'reversed'),
                             foot)
        self.set_focus_path(['footer',1])
        self._focus=True
        urwid.connect_signal(self.input,'line_entered',self.on_line_entered)
        self._output_styles=[s[0] for s in self.PALLETE]
        self.eloop=None
        delim=" "
        path=delim.join(sys.argv[1:])
        self.process=pexpect.spawn(self.setpath(), timeout=32767, encoding='utf-8')
        self._stopped=False

    def setpath(self):
        #check if file exists
        #if it does read from it
        #else take from args
        #if !(arg): err
        if(os.path.exists("terminal.conf")):
            with open("terminal.conf") as file:
                return file.readline()#[5:-2]
        elif((sys.argv[1:])):
            delim=" "
            path=delim.join(sys.argv[1:])
            with open("terminal.conf", "w+") as file:
                file.write(path)
                return path
        else:
            print("No command provided for starting server. Specify the shell command to start the server either as a command line argument or in a file 'terminal.conf'\nExiting!")
            quit()

    def loop(self, handle_mouse=False):
        self.eloop=urwid.MainLoop(self, self.PALLETE, handle_mouse=handle_mouse)
        self._eloop_thread=threading.current_thread()
        self.eloop.run()

    def on_line_entered(self,line):                 #handle terminal commands, or send them to application
        if line in ['quit', 'exit']:
            if(self._stopped):
                self.process.sendline("stop")
                time.sleep(5)
            raise urwid.ExitMainLoop()

        if line in ['fquit', 'fexit']:
            raise urwid.ExitMainLoop()

        if line in ['cls', 'clear']:
            self.body.clear()
            return

        if(line=="start"):
            self.body.clear()
            with threading.Lock():
                self.output("Starting Server...", "CLIENT")
                self.process=pexpect.spawn(self.setpath(), timeout=32767, encoding='utf-8')
                reader=Thread(target=read, args=(console.process,), daemon=True)
                reader.start()
                return

        if(line!=""):
            self.process.sendline(line)

    def output(self, line, style=None):
        if style and style in self._output_styles:
                line=(style,line)
        self.body.add(line)
        #since output could be called asynchronously form other threads we need to refresh screen in these cases
        if self.eloop and self._eloop_thread != threading.current_thread():
            self.eloop.draw_screen()


    def _update_focus(self, focus):
        self._focus=focus

    def switch_focus(self):
        if self._focus:
            self.set_focus('body')
            self._focus=False
        else:
            # TODO: set body focus to last line
            self.set_focus_path(['footer',1])
            self._focus=True

    def keypress(self, size, key):
        if key=='tab':
            self.switch_focus()
        return urwid.Frame.keypress(self, size, key)

console=Console(title='Terminal Client', max_size=32767, command_caption="Tab to switch focus to server log.(To scroll text)") #init class

def read(child):
    global reader
    console.output("Reading Console Output!", "CLIENT")
    while True:
        console._stopped = not reader.is_alive()
        out=child.readline()[:-2]
        out=out.replace("\t","  ")
        if(out !=""):
            if("INFO" in out):
                console.output(out, "INFO")
            elif("WARN" in out):
                console.output(out, "WARN")
            elif("ERROR" in out):
                console.output(out, "ERROR")
            else:
                console.output(out)
reader=Thread(target=read, args=(console.process,), daemon=True)
reader.start()

console.loop()
os.system('cls' if os.name == 'nt' else 'clear')
print("---QUIT---")
