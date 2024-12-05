from dataclasses import dataclass, field
from web3 import Web3


@dataclass
class Account:
    address: str
    private_key: str
    shorten_address: str = field(init=False)

    @classmethod
    def from_dict(cls, data):
        return cls(
            address=Web3.to_checksum_address(data.get("address")),
            private_key=data.get("private_key"),
        )

    def __post_init__(self):
        self.shorten_address = self.address[:4] + "..." + self.address[-4:]
