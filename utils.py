from web3 import Web3
from web3.middleware import geth_poa_middleware
from classes import Account
import json
import constants
import ERC20


def connect_web3(endpoint: str) -> Web3.HTTPProvider | None:
    """
    :param endpoint: RPC endpoint
    :return: web3 connector object
    """
    try:
        provider = Web3(Web3.HTTPProvider(endpoint))
        provider.middleware_onion.inject(geth_poa_middleware, layer=0)
        if provider.is_connected():
            return provider
    except ConnectionError:
        print(f"Failed to connect to {endpoint}")
        return None


def abi_loader(file_path: str) -> any:
    """
    :param file_path: file path of json file
    :return: json object of contract abi
    """
    with open(file_path) as f:
        return json.load(f)


def create_erc20(
    provider,
    name,
    symbol,
    supply=constants.ERC20_SUPPLY,
    decimals=18,
    signer=constants.SIGNER,
    signer_pkey=constants.SIGNER_PKEY,
) -> str | None:
    token_contract = provider.eth.contract(abi=ERC20.abi, bytecode=ERC20.bytecode)
    construct_tx = token_contract.constructor(
        name=name, symbol=symbol, _decimals=decimals, supply=supply
    ).build_transaction(
        {"nonce": provider.eth.get_transaction_count(signer), "gas": 10_000_000}
    )

    signed = provider.eth.account.sign_transaction(
        construct_tx,
        signer_pkey,
    )

    tx_hash = provider.eth.send_raw_transaction(signed.rawTransaction)
    tx_receipt = provider.eth.wait_for_transaction_receipt(tx_hash)

    if tx_receipt["contractAddress"]:
        return tx_receipt["contractAddress"]
    else:
        print("Failed to deploy token")
        return None


def contract_loader(provider, contract_address, abi):
    """
    :param provider: web3 provider object
    :param contract_address: contract address
    :param abi: contract abi
    :return: contract object of contract abi
    """
    checksum_addr = Web3.to_checksum_address(contract_address)
    return provider.eth.contract(address=checksum_addr, abi=abi)


def get_contract_instance(provider, contract_address):
    """
    :param provider: web3 provider object
    :param contract_address: contract address
    :param file_path: file path of contract abi
    :return: contract abi object, contract instance
    """
    contract_abi = ERC20.abi
    contract_instance = contract_loader(provider, contract_address, contract_abi)

    return {"abi": contract_abi, "instance": contract_instance}


def get_json(path):
    with open(path, "r") as file:
        return json.load(file)


def create_new_account(provider) -> Account:
    acc = provider.eth.account.create()

    return Account(address=acc.address, private_key=provider.to_hex(acc.key))
