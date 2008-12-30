# -*- coding: utf-8 -*-
#
# PyINIEditor by Pekka Järvinen 2008
# http://code.google.com/p/pyinieditor/
# Edit INI files from CLI

import os, sys, locale, traceback, tempfile, shutil, time
from ConfigParser import ConfigParser
from optparse import OptionParser, Option, OptionGroup

__VERSION__ = "0.1.0"
__AUTHOR__ = u"Pekka Järvinen"
__YEAR__ = 2008
__HOMEPAGE__ = u"http://code.google.com/p/pyinieditor/"

TYPE_GET    = 0x01
TYPE_SET    = 0x02
TYPE_REMOVE = 0x04

ERROR_NO_ERROR = 0x00
ERROR_ITEM_NOT_FOUND = 0x01
ERROR_SECTION_NOT_FOUND = 0x02
ERROR_FILE_NOT_FOUND = 0x04
ERROR_INVALID_PARAMS = 0x08

RETURN = ERROR_NO_ERROR

banner  = u"Python INI Editor - pyINIEditor ver. %s" % (__VERSION__)
banner += u" (c) %s %s" % (__AUTHOR__, __YEAR__)

examples = []
examples.append("")
examples.append(u"# %prog --get --file trac.ini")
examples.append(u"Output: whole trac.ini")
examples.append("")
examples.append(u"# %prog --get --file trac.ini --get-sections")
examples.append(u"Output: List of sections")
examples.append("")
examples.append(u"# %prog --get --file trac.ini --section trac")
examples.append(u"Output: List of section 'trac' items and values")
examples.append("")
examples.append(u"# %prog --get --file trac.ini --section trac --item database")
examples.append(u"Output: List of section 'trac' item 'database' item name and value")
examples.append("")
examples.append(u"# %prog --get --file trac.ini --separator \" >> \"")
examples.append(u"Output: Whole trac.ini with different item separator")
examples.append("")
usage = "\n".join(examples)

parser = OptionParser(version="%prog " + __VERSION__, usage=usage, description=banner)

parser.add_option("--get", action="store_const", const=TYPE_GET, dest="type", help="Get INI options from file")
parser.add_option("--set", action="store_const", const=TYPE_SET, dest="type", help="Set INI options to file")
parser.add_option("--remove", action="store_const", const=TYPE_REMOVE, dest="type", help="Remove INI section or item from file")

parser.add_option("--file", "-f", action="append", type="string", dest="filename", help="File name, ex: 'config.ini'")
parser.add_option("--section", "-s", action="store", type="string", dest="section", help="Section name ex: 'network'")
parser.add_option("--item", "-i", action="store", type="string", dest="item", help="Item name ex: 'ip_address'")
parser.add_option("--verbose", "-v", action="store_true", dest="verbose", help="Output more information", default=False)
parser.add_option("--separator", action="store", type="string", dest="separator", help="Separator ex: ' = ', ': '", default=" = ")

group = OptionGroup(parser, "--get")
group.add_option("--get-sections", action="store_true", dest="getsections", help="Get section names", default=False)
group.add_option("--get-item-names", action="store_true", dest="itemnamesonly", help="Get item names only", default=False)
group.add_option("--get-value", action="store_true", dest="valueonly", help="Get value only", default=False)
parser.add_option_group(group)

group = OptionGroup(parser, "--set")
group.add_option("--value", action="store", type="string", dest="value", help="Item value ex: '127.0.0.1'")
group.add_option("--print-section", action="store_true", dest="printsection", help="Print section ex: '[defaults]'", default=False)
group.add_option("--force", action="store_true", dest="forcecreation", help="Force creation if section doesn't exist", default=False)
parser.add_option_group(group)

(options, args) = parser.parse_args()

# Create temporary file
def filetemp():
  (fd, fname) = tempfile.mkstemp(text=True, prefix="config-", suffix=".ini.tmp")
  return (os.fdopen(fd, "w+"), fname)

# Get values
if options.type == TYPE_GET:
  if options.filename != None and len(options.filename) == 1:
    options.filename = os.path.realpath(options.filename[0])
    if os.path.isfile(options.filename):
      try:
        config = ConfigParser()
        config.read(options.filename)
        sections = config.sections()

        if options.getsections:
          for i in sections:
            print u"[%s]" % (i)
          print
        else:
          if options.section == None:
            # List all sections
            for s in sections:
              items = config.items(s)
              print u"[%s]" % (s)
              for i in items:
                key,val = i
                print u"%s%s%s" % (key, options.separator, val)
              print
          else:
            # List given section items
            if options.section in sections:
              if options.printsection:
                print u"[%s]" % (options.section)
              items = config.items(options.section)
              
              if options.item == None:
                # List all items
                for i in items:
                  key,val = i
                  if options.itemnamesonly:
                    print u"%s" % (key)
                  else:
                    print u"%s%s%s" % (key, options.separator, val)
                print
              else:
                # List given item
                keys = []
                for i in items:
                  key,val = i
                  keys.append(key)

                if options.item in keys:
                  for i in items:
                    key,val = i
                    if key == options.item:
                      if options.valueonly:
                        print val
                      else:
                        print u"%s%s%s" % (key, options.separator, val)
                      break
                  print
                else:
                  RETURN = RETURN | ERROR_ITEM_NOT_FOUND
                  print u"Item '%s' not found in section '%s'!" % (options.item, options.section)
            else:
              RETURN = RETURN | ERROR_SECTION_NOT_FOUND
              print u"Section '%s' not found!" % options.section
      except Exception, inst:
        print type(inst)
        print inst.args
        print inst
    else:
      RETURN = RETURN | ERROR_FILE_NOT_FOUND
      print "File not found: '%s'" % options.filename 
  else:
    RETURN = RETURN | ERROR_INVALID_PARAMS
    print u"--file missing or too many --file parameters. Try --help"

# Set values
elif options.type == TYPE_SET:
  if options.filename != None and len(options.filename) == 1:
    options.filename = os.path.realpath(options.filename[0])
    if os.path.isfile(options.filename):
      try:
        config = ConfigParser()
        config.read(options.filename)

        if not config.has_section(options.section) and options.forcecreation:
          config.add_section(options.section)

        if config.has_section(options.section):
          config.set(options.section, options.item, options.value)

          # Generate .bak file name
          renfn = "%s.bak" % options.filename
          if os.path.isfile(renfn):
            renfn = "%s-%s" % (renfn, time.time())
  
          tf, tfpath = filetemp()
          
          if options.verbose:
            print "; TEMPORARY FILENAME = %s" % tfpath
  
          # Write configuration
          config.write(tf)
  
          # Close file
          tf.close()
  
          # Rename .ini to .ini.bak
          shutil.move(options.filename, renfn)
  
          # Move temporary file to .ini
          shutil.move(tfpath, options.filename)
  
          # Remove .bak
          os.unlink(renfn)

        else:
          RETURN = RETURN | ERROR_SECTION_NOT_FOUND
          print u"Section '%s' not found! Use --force to create." % options.section
        
      except Exception, inst:
        print type(inst)
        print inst.args
        print inst
    else:
      print "File not found: '%s'" % options.filename 
  elif options.filename != None and len(options.filename) > 1:
    RETURN = RETURN | ERROR_INVALID_PARAMS
    print u"Too many --file parameters. Try --help"
  else:
    RETURN = RETURN | ERROR_INVALID_PARAMS
    print u"--file missing. Try --help"

# Remove values
elif options.type == TYPE_REMOVE:
  if options.filename != None and len(options.filename) == 1:
    options.filename = os.path.realpath(options.filename[0])
    if os.path.isfile(options.filename):
      try:
        config = ConfigParser()
        config.read(options.filename)

        if options.item != None and config.has_section(options.section) and config.has_option(options.section, options.item) and options.section != None:
          # Remove item
          config.remove_option(options.section, options.item)
          if options.verbose:
            print "; Removed item '%s' from section '%s'" % (options.item, options.section)

        elif options.section != None and config.has_section(options.section) and options.item == None:
          # Remove whole section
          config.remove_section(options.section)
          if options.verbose:
            print "; Removed section '%s'" % options.section

        # Generate .bak file name
        renfn = "%s.bak" % options.filename
        if os.path.isfile(renfn):
          renfn = "%s-%s" % (renfn, time.time())

        tf, tfpath = filetemp()
        
        if options.verbose:
          print "; TEMPORARY FILENAME = %s" % tfpath

        # Write configuration
        config.write(tf)

        # Close file
        tf.close()

        # Rename .ini to .ini.bak
        shutil.move(options.filename, renfn)

        # Move temporary file to .ini
        shutil.move(tfpath, options.filename)

        # Remove .bak
        os.unlink(renfn)

      except Exception, inst:
        print type(inst)
        print inst.args
        print inst

    else:
      RETURN = RETURN | ERROR_FILE_NOT_FOUND
      print u"File not found: '%s'" % options.filename 
  else:
    RETURN = RETURN | ERROR_INVALID_PARAMS
    print u"--file missing or too many --file parameters. Try --help"
     
# Print info
else:
  RETURN = RETURN | ERROR_INVALID_PARAMS
  print banner
  print
  parser.print_help()
  print
  print u"Send bugs and feature requests to <URL: %s >" % (__HOMEPAGE__)
  print

sys.exit(RETURN)
