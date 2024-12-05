from pydantic import BaseModel
from web3 import Web3
from typing import List, Any
from prettytable import PrettyTable
from network import conn
from account import Account
import constants
import utils
import config
import statistics
import time

DEBUG = True


class Token(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    name: str = None
    symbol: str = None
    supply: int = None
    decimals: int = None
    signer: str = None
    signer_pkey: str = None
    token_address: str = None
    contract: Any = None
    owner: str = None

    def __init__(
        self,
        name,
        symbol,
        supply=constants.ERC20_SUPPLY,
        decimals=18,
        signer=constants.SIGNER,
        signer_pkey=constants.SIGNER_PKEY,
        debug=DEBUG,
    ) -> None:
        token_address = utils.create_erc20(
            provider=conn,
            name=name,
            symbol=symbol,
            supply=supply,
            decimals=decimals,
            signer=signer,
            signer_pkey=signer_pkey,
        )
        if token_address:
            _contract = utils.get_contract_instance(conn, token_address)["instance"]
            super().__init__(
                token_address=token_address, owner=signer, contract=_contract
            )
            self.token_address = token_address
            self.contract = _contract
            self.owner = signer
            self.name = name
            self.symbol = symbol
            self.supply = supply
            self.decimals = decimals

            if debug:
                print(
                    f"[Token] New token {symbol}({token_address[:6]}...) created by admin"
                )

    def __repr__(self) -> str:
        return f"address: {self.token_address}\nname: {self.name}\nsymbol: {self.symbol}\nsupply: {self.supply}\ndecimals: {self.decimals}\nowner: {self.owner}"

    def __eq__(self, other):
        return self.token_address.lower() == other.token_address.lower()

    def balance_of_wei(self, acc: Account) -> int:
        return self.contract.functions.balanceOf(acc.address).call()

    def balance_of(self, acc: Account) -> float:
        balance_in_wei = self.balance_of_wei(acc)
        if balance_in_wei > 0:
            return self.balance_of_wei(acc) / 10**self.decimals
        else:
            return 0.0

    def approve(
        self,
        signer: Account,
        spender: str,
        amount: int,
        debug=DEBUG,
    ):
        tx = self.contract.functions.approve(spender, amount).build_transaction(
            {
                "from": signer.address,
                "nonce": conn.eth.get_transaction_count(signer.address),
                "gasPrice": conn.to_wei("30", "gwei"),
            }
        )
        signed_tx = conn.eth.account.sign_transaction(tx, signer.private_key)
        tx_hash = conn.eth.send_raw_transaction(signed_tx.rawTransaction)

        if debug:
            print(
                f"[Token] {signer.shorten_address} approved {amount} {self.symbol} for spender: {spender[0:4] + '...' + spender[-4:]} (txHash: {tx_hash.hex()[:4] + '...' + tx_hash.hex()[-4:]})"
            )

    def allowance(self, owner: Account, spender: str, debug=DEBUG):
        return self.contract.functions.allowance(owner.address, spender).call()

    def approve_if_necessary(
        self, _from: Account, _to: Account, amount: int, debug=DEBUG
    ):
        eth = Eth()
        curr_allowance = self.allowance(_from, _to.address)
        eth_balance = eth.check_balance(_from)
        if eth_balance < config.GAS_AMOUNT:
            to_be_sent = config.GAS_AMOUNT - eth_balance
            eth.send_eth(
                Account(constants.SIGNER, constants.SIGNER_PKEY),
                _from.address,
                to_be_sent,
            )

        to_be_approved = amount - curr_allowance
        if to_be_approved > 0:
            if debug:
                print(
                    f"[Token] Insuff. allowance, Amount need to be approved: {to_be_approved}"
                )
            self.approve(_from, constants.SIGNER, to_be_approved)

    def transfer(self, _from: Account, _to: Account, amount: int, debug=DEBUG):
        eth = Eth()
        eth_balance = eth.check_balance(_from)
        if eth_balance < config.GAS_AMOUNT:
            to_be_sent = config.GAS_AMOUNT - eth_balance
            eth.send_eth(
                Account(constants.SIGNER, constants.SIGNER_PKEY),
                _from.address,
                to_be_sent,
            )
        tx = self.contract.functions.transfer(_to.address, amount).build_transaction(
            {
                "from": _from.address,
                "nonce": conn.eth.get_transaction_count(_from.address),
                "gas": 20_000_000,
            }
        )
        gas = conn.eth.estimate_gas(tx)
        tx.update({"gas": gas})
        signed_tx = conn.eth.account.sign_transaction(tx, _from.private_key)
        tx_hash = conn.eth.send_raw_transaction(signed_tx.rawTransaction)
        if debug:
            print(
                f"[Token] {_from.shorten_address} transferred {amount/10**self.decimals} {self.symbol} to {_to.shorten_address} (txHash: {tx_hash.hex()[:4] + '...' + tx_hash.hex()[-4:]})"
            )

    def transfer_from(self, _from: Account, _to: Account, amount: int, debug=DEBUG):
        self.approve_if_necessary(_from, _to, amount)

        tx = self.contract.functions.transferFrom(
            _from.address, _to.address, amount
        ).build_transaction(
            {
                "from": _from.address,
                "nonce": conn.eth.get_transaction_count(_from.address),
                "gas": 0,
            }
        )
        gas = conn.eth.estimate_gas(tx)
        tx.update({"gas": gas})
        signed_tx = conn.eth.account.sign_transaction(tx, _from.private_key)
        tx_hash = conn.eth.send_raw_transaction(signed_tx.rawTransaction)

        if debug:
            print(
                f"[Token] {amount/10**self.decimals} {self.symbol} was transferred from {_from.shorten_address} to {_to.shorten_address} (txHash: {tx_hash.hex()[:4] + '...' + tx_hash.hex()[-4:]})"
            )

    def withdraw_all(self, acc: Account, debug=DEBUG) -> None:
        balance_in_wei = self.balance_of_wei(acc)
        if balance_in_wei > 0:
            admin = Account(constants.SIGNER, constants.SIGNER_PKEY)
            self.transfer(acc, admin, balance_in_wei)
            if debug:
                print(
                    f"[Token] {acc.shorten_address} transferred {balance_in_wei/10**18} {self.symbol} back to admin"
                )


class Eth:
    def __init__(self):
        pass

    def check_balance(self, acc: Account) -> int:
        checksum_addr = conn.to_checksum_address(acc.address)
        return conn.eth.get_balance(checksum_addr)

    def send_eth(self, sender: Account, dest: str, value: int, debug=DEBUG):
        tx = {
            "from": sender.address,
            "to": dest,
            "value": value,
            "nonce": conn.eth.get_transaction_count(sender.address),
            "gas": 0,
            "gasPrice": conn.to_wei("30", "gwei"),
        }

        gas = conn.eth.estimate_gas(tx)
        tx.update({"gas": gas})
        signed = conn.eth.account.sign_transaction(tx, sender.private_key)

        tx_hash = conn.eth.send_raw_transaction(signed.rawTransaction)
        if debug:
            print(
                f"[ETH] {sender.shorten_address} transferred {value/10**18} ETH to {dest[:4] + '...' + dest[-4:]} (txHash: {tx_hash.hex()[:4] + '...' + tx_hash.hex()[-4:]})"
            )


class Sweeper(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    whitelist_token: List[Token] = None
    acc_list: List[Account] = None
    provider: Web3.HTTPProvider = None

    def __init__(self):
        super().__init__()
        self.whitelist_token = []
        self.acc_list = []

    def add_token(self, token: Token, debug=DEBUG):
        self.whitelist_token.append(token)
        if debug:
            print(
                f"[Sweeper] New token {token.symbol}({token.token_address}) added to whitelist"
            )

    def add_acc(self, acc: Account, debug=DEBUG):
        self.acc_list.append(acc)
        if debug:
            print(f"[Sweeper] New acc {acc.shorten_address} added to sweeper")

    def remove_token(self, rm_token: Token, debug=DEBUG) -> bool:
        for token in self.whitelist_token:
            if token == rm_token:
                self.whitelist_token.remove(token)
                if debug:
                    print(
                        f"[Sweeper] Token {token.symbol}({token.token_address}) removed from whitelist"
                    )
                return True
        if debug:
            print(
                f"[Sweeper] {token.symbol}({token.token_address}) not found in whitelist"
            )
        return False

    def print_balance(self, acc: Account):
        table = PrettyTable()
        symbols = [i.symbol for i in self.whitelist_token]
        table.field_names = ["address", "eth", *symbols]

        row = []
        row.append(acc.shorten_address)
        eth = Eth()
        eth_balance = eth.check_balance(acc)
        row.append(str(eth_balance / 10**18) if eth_balance > 0 else "0.0")
        for t in self.whitelist_token:
            row.append((t.balance_of(acc)))
        table.add_row(row)
        print(table)

    def est_gas_price(self, debug=DEBUG):
        curr_block = conn.eth.get_block_number()
        tx_cnt = conn.eth.get_block_transaction_count(curr_block)

        gas_prices = []
        # estimate gas price from the first 10 tx
        for idx in range(min(tx_cnt, 10)):
            tx = conn.eth.get_transaction_by_block(curr_block, idx)
            gas_prices.append(tx["gasPrice"])

        median_gas_price = statistics.median(gas_prices)
        if debug:
            print(f"[Sweeper] median gas price from latest 10 tx: {median_gas_price}")
        return median_gas_price

    # send gas from the admin to the account
    def send_gas(
        self, sender: Account, dest: str, value: int = config.GAS_AMOUNT, debug=DEBUG
    ):
        eth = Eth()
        eth.send_eth(sender, dest, value)
        if debug:
            print(
                f"[Sweeper] {value/10**18} of ETH is sent to {dest[:4] + '...' + dest[-4:]} for the gas fee."
            )

    # return gas back to the admin
    def withdraw_gas(self, sender: Account, dest: str = constants.SIGNER, debug=DEBUG):
        eth = Eth()
        current_eth_bal = eth.check_balance(sender)
        tx = {
            "from": sender.address,
            "to": dest,
            "value": 1,
            "nonce": conn.eth.get_transaction_count(sender.address),
            "gas": 0,
            "gasPrice": 0,
        }
        gas = conn.eth.estimate_gas(tx)
        gas_price = self.est_gas_price()
        tx.update({"gas": gas, "gasPrice": gas_price})

        # extra 0.3% for the buffer
        total_gas = int(gas * gas_price * 1.1)
        amount = current_eth_bal - total_gas

        # only dust left, just leave it here
        if amount < 0:
            print(f"[Sweeper] Insuffient gas for account: {sender.address}")
            return

        eth.send_eth(
            sender,
            dest,
            amount,
        )

        if debug:
            print(
                f"[Sweeper] {amount/10**18} of ETH is returned back to admin from {sender.address}"
            )

    def get_balances_breakdown(self, acc: Account):
        if acc is None:
            return
        balances = []
        # @TODO Add pricefeed for ETH, now assuming every eth = $1 USD
        eth = Eth()
        eth_balance_wei = eth.check_balance(acc)
        eth_balance = eth_balance_wei / 10**18 if eth_balance_wei > 0 else 0.0
        balances.append({"token": "ETH", "amount": eth_balance})

        # @TODO Add pricefeed for tokens, now assuming every eth = $1 USD
        for t in self.whitelist_token:
            balance = t.balance_of(acc)
            balances.append({"token": t.symbol, "amount": balance})

        return balances

    def get_acc(self, address: str) -> Account | None:
        for acc in self.acc_list:
            if acc.address.lower() == address.lower():
                return Account(Web3.to_checksum_address(acc.address), acc.private_key)

    def handle_new_tx(self, address: str):
        print("[Sweeper] Start sweeping:", address)
        acc = self.get_acc(address)
        if acc is None:
            print(f"[Sweeper] Account not found: {address}")
            return
        self.print_balance(acc)
        breakdown = self.get_balances_breakdown(acc)
        total_amount_usd = sum(
            [float(i["amount"]) for i in breakdown] if len(breakdown) > 0 else 0.0
        )

        est_gas = self.est_gas_price()
        # Only sweep when gas is cheap
        if est_gas > config.MAX_GAS_PRICE:
            print(
                f"[Sweeper] Gas price too high, current: {est_gas}, max: {config.MAX_GAS_PRICE}"
            )
            return None

        if total_amount_usd < config.MINIMUM_AMOUNT_USD:
            print(
                f"[Sweeper] Insufficent balances. total balance in usd: {total_amount_usd}, min: {config.MINIMUM_AMOUNT_USD}"
            )
            return None

        for t in self.whitelist_token:
            t.withdraw_all(acc)

        time.sleep(2)
        self.withdraw_gas(sender=acc)

        print("[Sweeper] End of sweeping.")
        self.print_balance(acc)
        print("========================")


class User(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    uid: str = None
    wallets: List[Account] = []

    def __init__(self, uid):
        super().__init__()
        self.uid = uid

    def __repr__(self):
        return_str = ""
        return_str += f"uid: {self.uid}\n"
        for i in self.wallets:
            return_str += f"acc: {i.address}, pk: {i.private_key}\n"
        return return_str

    # generate a new wallet for the users
    def add_wallet(self, debug=DEBUG) -> Account:
        new_acc = utils.create_new_account(conn)
        self.wallets.append(new_acc)

        if debug:
            print(
                f"[User] user {self.uid} created new wallet: {new_acc.shorten_address}, # of wallet: {len(self.wallets)}"
            )
        return new_acc

    def add_wallets(self, num) -> List[Account]:
        acc = []
        for i in range(num):
            acc.append(self.add_wallet())
        return acc
