from web3 import Web3
from web3.middleware import geth_poa_middleware
from config import PORT

endpoint = f"http://127.0.0.1:{PORT}"
conn = Web3(Web3.HTTPProvider(endpoint))
conn.middleware_onion.inject(geth_poa_middleware, layer=0)
