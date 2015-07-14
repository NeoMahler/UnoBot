#!/usr/bin/env python
"""
ATENCIÓ: NO EDITIS AQUEST FITXER.
Executa ./phenny, després edita ~/.phenny/default.py
Després executa ./phenny una altra vegada
"""

import sys, os, imp, optparse
from textwrap import dedent as trim

dotdir = os.path.expanduser('config')

def check_python_version(): 
   if sys.version_info < (2, 4): 
      error = 'Error: You need Python 2.4 or later. Download it on www.python.org'
      print >> sys.stderr, error
      sys.exit(1)

def create_default_config(fn): 
   f = open(fn, 'w')
   print >> f, trim(u"""\
   nick = 'UnoBot'
   host = 'irc.example.net'
   channels = ['#example', '#test']
   owner = 'yournickname'

   # password is the NickServ password, serverpass is the server password
   # password = 'example'
   # serverpass = 'serverpass'

   # These are people who will be able to use admin.py's functions...
   admins = [owner, 'someoneyoutrust']
   # But admin.py is disabled by default, as follows:
   exclude = ['admin']

   # If you want to enumerate a list of modules rather than disabling
   # some, use "enable = ['example']", which takes precedent over exclude
   # 
   # enable = []

   # Directories to load user modules from
   # e.g. /path/to/my/modules
   extra = []

   # Services to load: maps channel names to white or black lists
   external = { 
      '#liberal': ['!'], # allow all
      '#conservative': [], # allow none
      '*': ['!'] # default whitelist, allow all
   }

   # EOF
   """)
   f.close()

def create_default_config_file(dotdir):
   print 'Creating a default config file at config/default.py...'
   default = os.path.join(dotdir, 'default.py')
   create_default_config(default)

   print 'Done; now you can edit default.py, and run phenny! Enjoy.'
   sys.exit(0)

def create_dotdir(dotdir): 
   print 'Creating a config directory at UnoBot/config...'
   try: os.mkdir(dotdir)
   except Exception, e: 
      print >> sys.stderr, 'There was a problem creating %s:' % dotdir
      print >> sys.stderr, e.__class__, str(e)
      print >> sys.stderr, 'Please fix this and then run phenny again.'
      sys.exit(1)

   create_default_config_file(dotdir)

def check_dotdir(): 
   default = os.path.join(dotdir, 'default.py')

   if not os.path.isdir(dotdir): 
      create_dotdir(dotdir)
   elif not os.path.isfile(default): 
      create_default_config_file(dotdir)

def config_names(config): 
   config = config or 'default'

   def files(d): 
      names = os.listdir(d)
      return list(os.path.join(d, fn) for fn in names if fn.endswith('.py'))

   here = os.path.join('.', config)
   if os.path.isfile(here): 
      return [here]
   if os.path.isfile(here + '.py'): 
      return [here + '.py']
   if os.path.isdir(here): 
      return files(here)

   there = os.path.join(dotdir, config)
   if os.path.isfile(there): 
      return [there]
   if os.path.isfile(there + '.py'): 
      return [there + '.py']
   if os.path.isdir(there): 
      return files(there)

   print >> sys.stderr, "Error: Couldn't find a config file!"
   print >> sys.stderr, 'What happened to ~/.phenny/default.py?'
   sys.exit(1)

def main(argv=None): 
   # Step One: Parse The Command Line

   parser = optparse.OptionParser('%prog [options]')
   parser.add_option('-c', '--config', metavar='fn', 
      help='use this configuration file or directory')
   opts, args = parser.parse_args(argv)
   if args: print >> sys.stderr, 'Warning: ignoring spurious arguments'

   # Step Two: Check Dependencies

   check_python_version() # require python2.4 or later
   if not opts.config:
      check_dotdir() # require ~/.phenny, or make it and exit

   # Step Three: Load The Configurations

   config_modules = []
   for config_name in config_names(opts.config): 
      name = os.path.basename(config_name).split('.')[0] + '_config'
      module = imp.load_source(name, config_name)
      module.filename = config_name

      if not hasattr(module, 'prefix'): 
         module.prefix = r'\.'

      if not hasattr(module, 'name'): 
         module.name = 'Phenny Palmersbot, http://inamidst.com/phenny/'

      if not hasattr(module, 'port'): 
         module.port = 6667

      if not hasattr(module, 'password'): 
         module.password = None

      if module.host == 'irc.example.net': 
         error = ('Error: you must edit the config file first!\n' + 
                  "You're currently using %s" % module.filename)
         print >> sys.stderr, error
         sys.exit(1)

      config_modules.append(module)

   # Step Four: Load Phenny

   try: from __init__ import run
   except ImportError: 
      try: from phenny import run
      except ImportError: 
         print >> sys.stderr, "Error: Couldn't find phenny to import"
         sys.exit(1)

   # Step Five: Initialise And Run The Phennies

   # @@ ignore SIGHUP
   for config_module in config_modules: 
      run(config_module) # @@ thread this

if __name__ == '__main__': 
   main()
