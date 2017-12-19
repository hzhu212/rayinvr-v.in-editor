import logging
logging.basicConfig(level=logging.DEBUG)
from editor import VmodelEditor


editor = VmodelEditor()
editor.mainloop()
