"""Note: we have modified the SendKeys code. Use the version packaged with PinkyTwirl."""

import os, sys
import re, types

from copy import deepcopy
from datetime import datetime

from SendKeys.SendKeys import SendKeys, CODES
from _sendkeys import toggle_numlock, key_down, key_up

import pythoncom, pyHook, ctypes

# Change this to reflect your choice of Left Alt-key remapping
Func = 'F12' 

# Sticky mode. Hitting this key puts PinkyTwirl into navigation mode (similar to vi normal mode). Hitting this key again switches off navigation mode.
StickyKey = 'Capital'

# When sticky mode is enabled, this key is implicitly pressed
DefaultFuncKey = Func

# This key completely switches on and off PinkyTwirl
ToggleKey = None

  
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
  GlobalState.CurFuncKey = AltSpace
  
KillLine = '{HOME}{HOME}+{END}{DEL}'
  
# A list of ambiguous keys. These keys can serve as regular keys, or as function keys.
# When one of these keys is pressed PinkyTwirl must wait for a second key to be pressed before disambiguating.
# If the second key pressed is part of a function key combo involving the first key, then the key combo is evaluated,
# otherwise both the first and second key are processed as normal keys.
AmbiguousKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']


# Function keys and their default mappings
# This is a nested dictionary. To look up a key combo, such as 2+K, first look up '2' then 'K'.
DefaultMap = {
  # Left Alt key, primarily used for navigation
  Func : {
    # Navigation
    'I' : '{UP}', 'J' : '{LEFT}', 'K' : '{DOWN}', 'L' : '{RIGHT}',
    'M' : '^{RIGHT}', 'N' : '^{LEFT}',
    'Oem_Comma' : '^[', 'Oem_Period' : '^]',
    '9' : '{PGUP}', '0' : '{PGDN}',
    'U' : '{HOME}', 'O' : '{END}', 'Y' : '{UP 12}', 'H' : '{DOWN 12}',
    'P' : '^{HOME}', 'Oem_1' : '^{END}',
    'Tab' : StartAltTab, 'F4' : AltF4,
    
    # Kill
    'Escape' : Kill,

    # Add line above current line
    'Return' : '{UP}{END}{ENTER}',
        
    # Goto def  # Find all ref  # Rename
    'F' : '^,', 'D' : '^.',     'S' : '^1',
    # Find      # Find and replace
    'A' : '^f', 'Q' : '^h',
    # undo      # Redo      # Paste
    'E' : '^z', 'R' : '^y', 'W' : '^v',
    
    # Special Alt + Space + AdditionalKey command. Once the function Space is ran, PinkyTwirl waits to hear for an additional third key.
    # This is a hack, and eventually robust support for 3-key combos will be added.
    'Space' : Space
    },

  # CAPS Lock key
  'Capital' : { },
    
  # Select/Highlight
  '4' : {
    'I' : '+{UP}', 'J' : '+{LEFT}', 'K' : '+{DOWN}', 'L' : '+{RIGHT}',
    'M' : '+^{RIGHT}', 'N' : '+^{LEFT}',
    #'9' : '+{PGUP}', '0' : '+{PGDN}',
    'U' : '+{HOME}', 'O' : '+{END}', 'Y' : '+{UP 12}', 'H' : '+{DOWN 12}',
    'P' : '+^{HOME}', 'Oem_1' : '+^{END}',

    # Copy      # Paste    # Cut
    'R' : '^c', 'T' : '^v', 'F' : '^x' },
  
  # Delete
  '3' : {
    'I' : '{UP}' + KillLine + KillLine,
    'J' : '{BS}', 'K' : KillLine, 'L' : '{DEL}',
    'M' : '+^{RIGHT}{DEL}', 'N' : '+^{LEFT}{DEL}',
    'U' : '+{HOME}{DEL}', 'O' : '+{END}{DEL}', 'Y' : '+{PGUP}{DEL}', 'H' : '+{PGDN}{DEL}' },
  
  # File tabs
  '2' : {
    # Switch        # Switch back    # Close all but this  # Close     # Save
    'J' : '^{TAB}', 'K' : '^+{TAB}', 'P' : '+^;',          'O' : '^;', 'I' : '^s' },
    
  # If Alt + Space was just pressed, process a third keystroke
  AltSpace : {
    'H' : '{ESC}{ESC}', 'J' : '^9^9', 'K' : '^8' }    
  }

# Simple map, used for applications where you don't want anything fancy.
# Because we are overriding some default Alt behavior, we still need to implement that basic functionality (Alt-Tab and Alt-F4)
SimpleMap = {
    Func : { 'Tab' : StartAltTab, 'F4' : AltF4 }
    }

# Visual Studios map
VisualStudioMap = deepcopy(DefaultMap)
VisualStudioMap[Func]['B'] = "^'"
VisualStudioMap['Capital']['J'] = '^mm'
VisualStudioMap[Func]['G'] = '^mm'

# Notepad map example. I use Notepad as a food diary, where I track my food, symptoms, and workout schedule. To facillitate data entry I use these shortcuts:
NotepadMap = deepcopy(DefaultMap)
NotepadMap[Func]['F'] = KillLine + '#Ate{SPACE}'
NotepadMap[Func]['D'] = KillLine + '#Data{SPACE}'
NotepadMap[Func]['S'] = KillLine + '#Action{SPACE}'
def Day():
  now = datetime.now()
  return '#Day{SPACE}%d-%d-%d{ENTER}{ENTER}' % (now.month, now.day, now.year)
NotepadMap[Func]['R'] = Day

# Command prompt. This overrides the tedious Alt-Space e p method for pasting with the default PinkyTwirl paste command Alt + W
CommandPromptMap = deepcopy(DefaultMap)
CommandPromptMap[Func]['W'] = '%{SPACE}ep'
CommandPromptMap['4']['R'] = '%{SPACE}es{ENTER}'
CommandPromptMap[Func]['A'] = '%{SPACE}ef{ENTER}'

# Notepad++
NotepadPlusPlusMap = deepcopy(DefaultMap)
NotepadPlusPlusMap['Capital']['J'] = NotepadPlusPlusMap[Func]['Oem_Comma'] = '^k'
NotepadPlusPlusMap['Capital']['K'] = NotepadPlusPlusMap[Func]['Oem_Period'] = '^+k'

WingIdeMap = deepcopy(NotepadPlusPlusMap)

LEdMap = deepcopy(NotepadPlusPlusMap)

# WinSCP is a barebones text editor I occasionally use to remotely edit Python files. It doesn't support spaced tabs, so instead PinkyTwirl replaces Tab with spaces.
WinSCP = deepcopy(DefaultMap)
WinSCP[None] = { }
WinSCP[None]['Tab'] = '{SPACE 4}'

# Chrome remapping. Quickly open and close tabs, as well as get to the Omnibox.
ChromeMap = deepcopy(DefaultMap)
ChromeMap[Func]['F'] = '^l'
ChromeMap['2']['O'] = '^w'
ChromeMap['2']['I'] = '^t'


# Application mapping. Determines which application gets which dictionary of commands.
# We take the name of the current window and look to see if it contains any of the following strings.
# If a match is found we use the associated dictionary. Matching works sequentially.
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
  """Convert a character to a PinkyTwirl specific index key."""
  
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
  """Store all global variables."""
  
  Toggle = True # Whether PinkyTwirl is activated
  StickyMode = False # Whether we are in sticky mode (similar to vim's normal mode)
  CapsLock = False # Whether CAPS lock is on

  Ambiguous = False # Whether the last key pressed was amibiguous
  AmbiguousKey = '' # If it was ambiguous, what key was it?
  
  # Store the current and previous state of all keys
  Key = [False for i in range(1000)]
  KeyPrev = [False for i in range(1000)]

  CurFuncKey = '' # The current function key being pressed, eg Alt, Ctrl, 3, 4, etc
  
  @classmethod
  def GetKeyState(cls, char):
    """Returns true if the given character key is currently down."""
    
    i = KeyToIndex(char)
    return cls.Key[i]
  
  @classmethod
  def GetKeyPressed(cls, char):
    """Returns true if the given character key was just pressed and was previously not pressed."""
    
    i = KeyToIndex(char)
    return cls.Key[i] and not cls.KeyPrev[i]

  @classmethod
  def SetKeyState(cls, char, state):
    """Updates whether a key is pressed or not."""
    
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
  """Called every time a KeyUp event is fired.
  Should return True if the intercepted up event should be allowed to pass on to the active application.
  Otherwise return False."""
  
  # Return if PinkyTwirl is not currently active
  if not GlobalState.Toggle: return True

  # Ignore Cntrl up messages while '2' function key is in use  
  # HACK, change this.
  # 2+J and 2+K invoke the Ctrl key to switch tabs, but we must suppress Ctrl up key events to prevent premature ending of the tab switching.
  # To do: Tab method should itself just not send Ctrl up key event (must modify SendKeys). Then always send a control up message when a the 2 key is released.
  if GlobalState.CurFuncKey == '2':
    if event.Key == 'Lcontrol':
      return False
  
  # Uncomment this for debugging purposes, to see what events are being fired.
  #print event.Key, event.KeyID
  
  # If the event was injected (programatically generated), then allow it to pass on
  if event.Injected != 0:
    return True

  # Send an Alt Key up message when the remapped Alt key is released
  if event.Key == Func:
    key_up(17)
    key_up(18)

  # StickyMode key is released
  # if event.Key == StickyKey:
    # GlobalState.StickyMode = False
    # return False

  # Update the array holding key state data
  GlobalState.SetKeyState(event.Key, False)

  # Get the map associated with this window
  FuncKeys = GetMap(event.WindowName)

  # If ambiguous then disamguoate
  if GlobalState.Ambiguous:
    # If the ambiguous function key is released before anything else is pressed,
    # then interpret the function key as a regular key
    if event.Key == GlobalState.CurFuncKey:
      GlobalState.Ambiguous = False
      SendKeys(GlobalState.AmbiguousKey)
      GlobalState.CurFuncKey = None
      return False

  # Find the previous functon key pressed
  PrevFuncKey = None
  if event.Key == GlobalState.CurFuncKey:
    for key in FuncKeys:
      if GlobalState.GetKeyState(key):
        PrevFuncKey = key
        break
  else:
    PrevFuncKey = GlobalState.CurFuncKey
      
  if GlobalState.StickyMode: 
    if PrevFuncKey == None: PrevFuncKey = DefaultFuncKey

  # If a function key was just released, use a previously pressed and still currently pressed function key as the active function key.
  if event.Key == GlobalState.CurFuncKey:
    GlobalState.CurFuncKey = PrevFuncKey
    key_up(17)
    key_up(18)

  # Note this is a hack to make Alt + Space work properly
  if event.Key == Func or event.Key == 'Space':
    GlobalState.CurFuncKey = None
    GlobalState.Ambiguous = False

  # Map the event if a function key is in use
  if GlobalState.CurFuncKey != None:
    return Map(event, ' Up')
  # Otherwise allow the event through unmodified
  else:
    return True

def OnKeyDown(event):
  # Uncomment this for debugging purposes, to see what events are being fired.
  #print event.WindowName
  #print event.Key, event.Ascii, chr(event.Ascii)
  
  # Check for the toggle key
  if event.Key == ToggleKey and ToggleKey != None:
    Toggle()
    return False
    
  # Return if PinkyTwirl is not currently active 
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
    if event.Key != GlobalState.CurFuncKey and not event.Key in FuncKeys[GlobalState.CurFuncKey]:        
      SendKeys(GlobalState.CurFuncKey)
      GlobalState.CurFuncKey = None
      return True

  # If the key is a function key, check to see if it is part of another function key's command
  SetAsFuncKey = False # Whether the key pressed should be interpreted as a function key
  if event.Key in FuncKeys:
    try:
      if not event.Key in FuncKeys[GlobalState.CurFuncKey]:
        SetAsFuncKey = True
    except:
        SetAsFuncKey = True

  if SetAsFuncKey:
    if GlobalState.CurFuncKey != event.Key and event.Key in AmbiguousKeys:
        GlobalState.Ambiguous = True
        GlobalState.AmbiguousKey = chr(event.Ascii)
    GlobalState.CurFuncKey = event.Key

  # Activate/Deactivate sticky mode
  if event.Key == StickyKey:
    if GlobalState.StickyMode:
      GlobalState.StickyMode = False
    else:
      GlobalState.StickyMode = True
      GlobalState.CurFuncKey = DefaultFuncKey
    return False
    
  # Enter and Space always end sticky mode
  if GlobalState.StickyMode:
    if event.Key == 'Return':
      GlobalState.StickyMode = False
      GlobalState.CurFuncKey = None

      # Make new line above current line if 'F' is pressed
      # THIS SHOULD NOT BE HARD CODED. REFACTOR THIS.
      if GlobalState.GetKeyState('F'):
        SendKeys('{UP}{END}{ENTER}')
        return False

      if event.Key == 'Launch_Mail':
        return False
        
      return True
  
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
  """Takes in a keyboard event and modifies it based on the currently pressed function key.
  Returns True if the original event should pass through to the target application.
  Returns False if the original event has been modified."""
  
  funcKey = GlobalState.CurFuncKey
  send = None

  # Get the dictionary associated with the current window
  FuncKeys = GetMap(event.WindowName)

  if funcKey in FuncKeys:
    # Get the shortcuts associated with the currently pressed function key
    item = FuncKeys[funcKey]

    # Get the action associated with the function key + pressed key combo (stored in the variable send)
    if type(item) == dict:
      lookup = event.Key + addon
      if lookup in item:
        send = item[lookup]
    elif event.Key == funcKey:
      send = item

  # If we have something to send
  if send != None:
    if type(send) == types.FunctionType:
      send = send()

    # Send the new command
    if send != None:
      SendKeys(send)

    # Don't let the old event pass through
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