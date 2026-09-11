from app import app
from app import create_app

app = create_app()

import sys
path = '/home/yourusername/yourprojectfolder'
if path not in sys.path:
    sys.path.append(path)

from app import app as application