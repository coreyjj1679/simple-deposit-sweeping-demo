import utils
import constants
from web3 import Web3
from classes import Account, Token

conn = utils.connect_web3("http://127.0.0.1:8080")


# load all EOA from json
accounts_json = utils.get_json("accounts.json")
accounts = [Account.from_dict(i) for i in accounts_json]


signer = accounts[0]
user_1 = accounts[1]
user_2 = accounts[2]


erc20_bytecode = constants.ERC20_BYTECODE
erc20_abi = utils.abi_loader("abis/ERC20.json")


# deploy dummy tokens
usdt = Token(conn, "Mock Tether USD", "MockUSDT")
usdc = Token(conn, "Mock USD Coin", "MockUSDC")


# burn all ETH in user1&2 to simulate real world situation

# transfer funds to user1&2


# start wss and sweep tokens from user1&2
