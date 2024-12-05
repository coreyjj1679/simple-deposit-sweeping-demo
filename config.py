MAX_BLOCK = 1_000  # All accounts must be swept after MAX_BLOCK blocks

MINIMUM_AMOUNT_USD = 50  # minimum amount of token in USD to be swept

# max gas price, stop sweeping when the network is in high traffic and gas is expensive
MAX_GAS_PRICE = 30_000_000_000  # 30 gwei

# amount of gas to be sent before sweeping
GAS_AMOUNT = 500_000_000_000_000_000  # 0.5ETH or 200000000000000000 wei

PORT = 8888
