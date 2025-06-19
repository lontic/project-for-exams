from .commands import setup_commands
from .messages import setup_messages
from .callbacks import setup_callbacks

def setup_handlers(application):
    setup_commands(application)
    setup_messages(application)
    setup_callbacks(application)