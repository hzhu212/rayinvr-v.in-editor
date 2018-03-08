import logging
import sys

from editor import VmodelEditor

log_level = logging.WARNING
if len(sys.argv) > 1 and sys.argv[1].lower() == '--debug':
	log_level = logging.DEBUG
if len(sys.argv) > 1 and sys.argv[1].lower() == '--info':
	log_level = logging.INFO

logging.basicConfig(level=log_level)

editor = VmodelEditor()
editor.mainloop()
