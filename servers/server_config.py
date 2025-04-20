import logging
from dotenv import load_dotenv

def setup_server(log_level=logging.DEBUG):
    load_dotenv()
    logging.basicConfig(level=log_level)