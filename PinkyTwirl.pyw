"""Note: we have modified the SendKeys code."""

import os, sys
import re, types

from copy import deepcopy
from datetime import datetime

from SendKeys.SendKeys import SendKeys, CODES
from _sendkeys import toggle_numlock, key_down, key_up

import pythoncom, pyHook, ctypes

ToggleKey = None
Func = 'F12' # Change this to reflect your choice of Left Alt-key remapping
StickyKey = None

# When sticky mode is enabled, this key is implicitly pressed
DefaultFuncKey = Func
  
def StartAltTab():
  """Send the Alt-Tab key string. (Alt down)(Tab down)(Tab up).
     Note that (Alt up) is not sent so that the tab explorer window stays open."""
  key_down(18)
  return '{TAB}'

def AltF4():
  """Send the Alt-F4 key string. (Alt down)(F4 down)(F4 up)"""
  key_down(18)
  return '{F4}'

def Kill():
  """Terminate the PinkyTwirl program."""
  ctypes.windll.user32.PostQuitMessage(0)

def Toggle():
  """Toggle PinkyTwirl on and off."""
  GlobalState.Toggle = not GlobalState.Toggle  

AltSpace = 'AltSpace'
def Space():
  GlobalState.gFuncKey = AltSpace
  
KillLine = '{HOME}{HOME}+{END}{DEL}'
  
# A list of ambiguous keys. These keys can server as regular keys, or as function keys.
# When one of these keys is pressed PinkyTwirl must wait for a second key to be pressed before disambiguating.
# If the second key pressed is part of a function key combo involving the first key, then the key combo is evaluated,
# otherwise both the first and second key are processed as normal keys.
AmbiguousKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']


# Function keys and their mappings
DefaultMap = {
  # Move
  Func : {  
    'Space' : Space,
    # Kill
    'Escape' : Kill,
    'I' : '{UP}', 'J' : '{LEFT}', 'K' : '{DOWN}', 'L' : '{RIGHT}',
    'M' : '^{RIGHT}', 'N' : '^{LEFT}',
    'Oem_Comma' : '^[', 'Oem_Period' : '^]',
    '9' : '{PGUP}', '0' : '{PGDN}',
    'U' : '{HOME}', 'O' : '{END}', 'Y' : '{UP 12}', 'H' : '{DOWN 12}',
    'P' : '^{HOME}', 'Oem_1' : '^{END}',
    'Tab' : StartAltTab, 'F4' : AltF4,
    'Return' : '{UP}{END}{ENTER}',
    # Goto def  # Find all ref  # Rename
    'F' : '^,', 'D' : '^.',     'S' : '^1',
    # Find      # Find and replace
    'A' : '^f', 'Q' : '^h',
    # undo      # Redo      # Paste
    'E' : '^z', 'R' : '^y', 'W' : '^v'  },

  # CAPS Lock key
  'Capital' : { },
    
  # Select
  '4' : {
    'I' : '+{UP}', 'J' : '+{LEFT}', 'K' : '+{DOWN}', 'L' : '+{RIGHT}',
    'M' : '+^{RIGHT}', 'N' : '+^{LEFT}',
    #'9' : '+{PGUP}', '0' : '+{PGDN}',
    'U' : '+{HOME}', 'O' : '+{END}', 'Y' : '+{UP 12}', 'H' : '+{DOWN 12}',
    'P' : '+^{HOME}', 'Oem_1' : '+^{END}',
    'Tab' : StartAltTab, 'F4' : AltF4,
    'Return' : '+{UP}{END}{ENTER}',
    # Copy      # Paste    # Cut
    'R' : '^c', 'T' : '^v', 'F' : '^x' },
  
  # Delete
  '3' : {
    'I' : '{UP}' + KillLine + KillLine, #'{UP}{HOME}+{END}{DEL}',
    'J' : '{BS}', 'K' : KillLine, 'L' : '{DEL}',
    'M' : '+^{RIGHT}{DEL}', 'N' : '+^{LEFT}{DEL}',
    'U' : '+{HOME}{DEL}', 'O' : '+{END}{DEL}', 'Y' : '+{PGUP}{DEL}', 'H' : '+{PGDN}{DEL}' },
  
  # File tabs
  '2' : {
    # Switch        # Switch back    # Close all but this  # Close     # Save
    'J' : '^{TAB}', 'K' : '^+{TAB}', 'P' : '+^;',          'O' : '^;', 'I' : '^s' },
    
  AltSpace : {
    'H' : '{ESC}{ESC}', 'J' : '^9^9', 'K' : '^8' }    
  }

SimpleMap = {
    Func : { 'Tab' : StartAltTab, 'F4' : AltF4 }
    }

VisualStudioMap = deepcopy(DefaultMap)
VisualStudioMap[Func]['B'] = "^'"
#VisualStudioMap[Func]['N'] = '^j'
#VisualStudioMap[Func]['M'] = '^l'
#VisualStudioMap['4']['N'] = '+^j'
#VisualStudioMap['4']['M'] = '+^l'
#VisualStudioMap['3']['N'] = '+^j{DEL}'
#VisualStudioMap['3']['M'] = '+^l{DEL}'
VisualStudioMap['Capital']['J'] = '^mm'
VisualStudioMap[Func]['G'] = '^mm'
    
NotepadMap = deepcopy(DefaultMap)
NotepadMap[Func]['F'] = KillLine + '#Ate{SPACE}'
NotepadMap[Func]['D'] = KillLine + '#Data{SPACE}'
NotepadMap[Func]['S'] = KillLine + '#Action{SPACE}'
def Day():
  now = datetime.now()
  return '#Day{SPACE}%d-%d-%d{ENTER}{ENTER}' % (now.month, now.day, now.year)
NotepadMap[Func]['R'] = Day

CommandPromptMap = deepcopy(DefaultMap)
CommandPromptMap[Func]['W'] = '%{SPACE}ep'
CommandPromptMap['4']['R'] = '%{SPACE}es{ENTER}'
CommandPromptMap[Func]['A'] = '%{SPACE}ef{ENTER}'

NotepadPlusPlusMap = deepcopy(DefaultMap)
NotepadPlusPlusMap['Capital']['J'] = NotepadPlusPlusMap[Func]['Oem_Comma'] = '^k'
NotepadPlusPlusMap['Capital']['K'] = NotepadPlusPlusMap[Func]['Oem_Period'] = '^+k'

WingIdeMap = deepcopy(NotepadPlusPlusMap)

LEdMap = deepcopy(NotepadPlusPlusMap)


WinSCP = deepcopy(DefaultMap)
WinSCP[None] = { }
WinSCP[None]['Tab'] = '{SPACE 4}'

ChromeMap = deepcopy(DefaultMap)
ChromeMap[Func]['F'] = '^l'
ChromeMap['2']['O'] = '^w'
ChromeMap['2']['I'] = '^t'


WindowMap = [
  ('Chrome', ChromeMap),
  ('C#', VisualStudioMap),
  ('Cloudberry', SimpleMap),
  ('POS Editor', SimpleMap),
  ('Notepad++', NotepadPlusPlusMap),
  ('Notepad', NotepadMap),
  ('Wing IDE', WingIdeMap),
  ('Command Prompt', CommandPromptMap),
  ('IPython', CommandPromptMap),
  ('LEd', LEdMap),
  ('/', WinSCP) ]


def KeyToIndex(char):
  if char == None: return 0
  
  if type(char) == str:
    if len(char) == 1:
      return ord(char)
    elif char == 'Space': return 1
    elif char == 'Lshift': return 2
    elif char == 'Rshift': return 3
    elif char == 'Lcontrol': return 4
    elif char == 'Capital': return 5
    elif char == 'Tab': return 6
    elif char == 'Return': return 7
    elif char == 'Lmenu': return 8
    elif char == 'Rmenu': return 9
    elif char == Func: return 10
    else:
      return 0
  else:
    return char

class GlobalState:
  Toggle = True

  Ambiguous = False
  AmbiguousKey = ''
  
  UpDown = 0
  
  Key = [False for i in range(1000)]
  KeyPrev = [False for i in range(1000)]

  gFuncKey = ''

  StickyMode = False
  CapsLock = False
  
  @classmethod
  def GetKeyState(cls, char):
    i = KeyToIndex(char)
    return cls.Key[i]
  
  @classmethod
  def GetKeyPressed(cls, char):
    i = KeyToIndex(char)
    return cls.Key[i] and not cls.KeyPrev[i]

  @classmethod
  def SetKeyState(cls, char, state):
    i = KeyToIndex(char)
    cls.KeyPrev[i] = cls.Key[i]
    cls.Key[i] = state

def GetMap(WindowName):
  """Finds the first partial window name in the WindowMap list
     that matches the current window, and returns
     the key map associated with that window."""

  if WindowName == None:
    WindowName = ''
      
  for name, keymap in WindowMap:
    if WindowName.find(name) >= 0:
      return keymap
	
  return DefaultMap

    
def OnKeyUp(event):
  if not GlobalState.Toggle: return True

  # change this. tab method should itself just not send cntrl key. then always send a control up message when a fnnction key is released
  # Ignore Cntrl up messages while '2' function key is in use
  if GlobalState.gFuncKey == '2':
    if event.Key == 'Lcontrol':
      return False
  
  #print event.Key, event.KeyID
  if event.Injected != 0:
    return True

  if event.Key == Func:
    key_up(17)
    key_up(18)
    GlobalState.StickyMode = False

  # StickyMode key
  if event.Key == StickyKey:
    GlobalState.StickyMode = False
    return False

  GlobalState.SetKeyState(event.Key, False)

  FuncKeys = GetMap(event.WindowName)

  # If ambiguous then disamguoate
  if GlobalState.Ambiguous:
    # If the ambiguous function key is released before anything else is pressed,
    # then interpret the function key as a regular key
    if event.Key == GlobalState.gFuncKey:
      GlobalState.Ambiguous = False
      #SendKeys(GlobalState.gFuncKey)
      SendKeys(GlobalState.AmbiguousKey)
      GlobalState.gFuncKey = None
      return False

  # Find the previous functon key pressed
  PrevFuncKey = None
  if event.Key == GlobalState.gFuncKey:
    for key in FuncKeys:
      if GlobalState.GetKeyState(key):
        PrevFuncKey = key
        break
  else:
    PrevFuncKey = GlobalState.gFuncKey
      
  if GlobalState.StickyMode: 
    if PrevFuncKey == None: PrevFuncKey = DefaultFuncKey

  if event.Key == GlobalState.gFuncKey:
    GlobalState.gFuncKey = PrevFuncKey
    key_up(17)
    key_up(18)

  # Note this is a hack to make Alt + Space work properly
  if event.Key == Func or event.Key == 'Space':
    GlobalState.gFuncKey = None
    GlobalState.Ambiguous = False
    
  if GlobalState.gFuncKey != None:
    return Map(event, ' Up')
  else:
    return True

def OnKeyDown(event):
  #print event.WindowName
  #print event.Key, event.Ascii, chr(event.Ascii)
  
  if event.Key == ToggleKey and ToggleKey != None:
    Toggle()
    return False
  if not GlobalState.Toggle: return True  
      
  # Skip events that we have injected
  if event.Injected != 0:
    return True

  # Get the current key mapping for this window
  FuncKeys = GetMap(event.WindowName)

  # If ambiguous then disambiguate
  if GlobalState.Ambiguous:
    GlobalState.Ambiguous = False

    # If the second key pressed isn't part of the function keys command,
    # and also isn't the function key itself (from holding it down and generating multiple down events)
    # then interpret the function key as a regular key
    if event.Key != GlobalState.gFuncKey and not event.Key in FuncKeys[GlobalState.gFuncKey]:        
      SendKeys(GlobalState.gFuncKey)
      GlobalState.gFuncKey = None
      return True

  # If the key is a function key, check to see if is part of another function key's command
  SetAsFuncKey = False # Whether the key pressed should be interpreted as a function key
  if event.Key in FuncKeys:
    try:
      if not event.Key in FuncKeys[GlobalState.gFuncKey]:
        SetAsFuncKey = True
    except:
        SetAsFuncKey = True

  if SetAsFuncKey:
    if GlobalState.gFuncKey != event.Key and event.Key in AmbiguousKeys:
        GlobalState.Ambiguous = True
        GlobalState.AmbiguousKey = chr(event.Ascii)
    GlobalState.gFuncKey = event.Key

  # Activate/Deactivate sticky mode
  if event.Key == StickyKey:
    if GlobalState.StickyMode:
      GlobalState.StickyMode = False
    else:
      GlobalState.StickyMode = True
      GlobalState.gFuncKey = DefaultFuncKey
    return False
    
  # Enter and Space always end sticky mode
  if GlobalState.StickyMode:
    if event.Key == 'Return':
      GlobalState.StickyMode = False
      GlobalState.gFuncKey = None

      # Make new line above current line if 'F' is pressed
      # THIS SHOULD NOT BE HARD CODED. REFACTOR THIS.
      if GlobalState.GetKeyState('F'):
        SendKeys('{UP}{END}{ENTER}')
        return False

      if event.Key == 'Launch_Mail':
        return False
        
      return True
    #if event.Key == 'Space':
      #GlobalState.StickyMode = False
      #GlobalState.gFuncKey = None
      
      #return False
  
  # Check for Shift-Shift to active CAPS (since CAPS is now our stickymode button)
  if event.Key == 'Lshift' and GlobalState.GetKeyState('Rshift') or event.Key == 'Rshift' and GlobalState.GetKeyState('Lshift'):
    SendKeys('{CAP}')
    GlobalState.CapsLock = not GlobalState.CapsLock
  
  # Update the state of the key just pressed
  GlobalState.SetKeyState(event.Key, True)

  if GlobalState.Ambiguous:
    return False

  return Map(event)

def Map(event, addon = ''):  
  funcKey = GlobalState.gFuncKey
  send = None

  FuncKeys = GetMap(event.WindowName)
  if funcKey in FuncKeys:
    item = FuncKeys[funcKey]
    
    if type(item) == dict:
      lookup = event.Key + addon
      if lookup in item:
        send = item[lookup]
    elif event.Key == funcKey:
      send = item

  if send != None:
    if type(send) == types.FunctionType:
      send = send()

    if send != None:
      SendKeys(send)

    return False

  if event.Key in FuncKeys:
    return False
  else:
    return True  
  
# Create a hook manager
hm = pyHook.HookManager()

hm.KeyDown = OnKeyDown
hm.KeyUp = OnKeyUp

# Set the hook
hm.HookKeyboard()
# Process messages forever
pythoncom.PumpMessages()



