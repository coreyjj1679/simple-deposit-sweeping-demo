from dataclasses import dataclass
import constants
import utils


@dataclass
class Account:
    address: str
    private_key: str

    @classmethod
    def from_dict(cls, data):
        return cls(address=data.get("address"), private_key=data.get("private_key"))


class Token:
    def __init__(
        self,
        provider,
        name,
        symbol,
        supply=constants.ERC20_SUPPLY,
        decimals=6,
        signer=constants.SIGNER,
        signer_pkey=constants.SIGNER_PKEY,
    ) -> None:
        token_address = utils.create_erc20(
            provider, name, symbol, supply, decimals, signer, signer_pkey
        )

        if token_address:
            self.token_address = token_address
            self.contract = utils.get_erc20_instance(provider, token_address)[
                "instance"
            ]
            self.owner = signer
            self.name = name
            self.symbol = symbol
            self.supply = supply
            self.decimals = decimals
            print(f"New token {token_address} created by {signer}")

    def __repr__(self) -> str:
        return f"address: {self.token_address}\nname: {self.name}\nsymbol: {self.symbol}\nsupply: {self.supply}\ndecimals: {self.decimals}\nowner: {self.owner}"

    def balance_of_wei(self, address) -> int:
        return self.contract.functions.balanceOf(address).call()

    def balance_of(self, address) -> float:
        balance_in_wei = self.balance_of_wei(address)
        if balance_in_wei > 0:
            return self.balance_of_wei(address) / 10**self.decimals
        else:
            return 0.0

    def transfer(self, _from: Account, _to: Account | str):
        pass


class Admin:
    def sweep():
        pass

    def send_gas():
        pass

    def withdraw_gas():
        pass


class User:
    id: str
    wallets = []

    # generate a new wallet for the users
    def add_wallet():
        pass

    def remove_wallet():
        pass
