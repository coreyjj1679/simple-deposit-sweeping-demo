from collections import defaultdict
import random
import time
import constants
import asyncio
from web3 import AsyncWeb3
from web3.providers import WebsocketProviderV2
from classes import Token, Sweeper, User
from account import Account
from network import conn
from threading import Thread
from config import PORT

sweeper = Sweeper()
wss_endpoint = f"ws://127.0.0.1:{PORT}"

user0 = User("peter2020")
user1 = User("billy1999")
accounts_user0 = user0.add_wallets(5)
accounts_user1 = user1.add_wallets(3)
for acc in accounts_user0 + accounts_user1:
    sweeper.add_acc(acc)

# # deploy dummy tokens
usdt = Token("Mock Tether USD", "MockUSDT")
usdc = Token("Mock USD Coin", "MockUSDC")
uni = Token("Mock Uniswap Token", "MockUNI")
tokens = [usdt, usdc, uni]


# # add token to white_list
sweeper.add_token(usdt)
sweeper.add_token(usdc)
sweeper.add_token(uni)


def main():
    signer = Account(constants.SIGNER, constants.SIGNER_PKEY)

    cnt = 0
    while True:
        random_token = random.choice(tokens)
        random_account = random.choice(sweeper.acc_list)
        random_amount = int(random.uniform(10, 500) * 10**18)

        random_token.transfer(signer, random_account, random_amount)
        time.sleep(5)
        cnt += 1

        if cnt >= 20:
            break


async def ws_v2_subscription_context_manager_example():
    last_update = defaultdict(int)
    async with AsyncWeb3.persistent_websocket(WebsocketProviderV2(wss_endpoint)) as w3:
        await w3.eth.subscribe("newHeads")
        async for response in w3.ws.process_subscriptions():
            tx_hashes = [i.hex() for i in response["result"]["transactions"]]
            for txh in tx_hashes:
                tx = conn.eth.get_transaction(txh)
                _to = "0x" + tx["input"].hex()[34:74]
                if _to and _to.lower() != constants.SIGNER.lower() and _to != "0x":
                    tx_block = int(tx["blockNumber"])
                    if tx_block - last_update[_to] > 5:
                        sweeper.handle_new_tx(_to)
                    last_update[_to] = tx_block


if __name__ == "__main__":
    Thread(target=main).start()
    asyncio.run(ws_v2_subscription_context_manager_example())
    # main()
