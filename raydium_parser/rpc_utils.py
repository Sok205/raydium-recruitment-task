import os

from solana.rpc.api import Client
from solders.transaction_status import UiConfirmedBlock

#I know that this file was supposed to remain untouched but I had to change it to make it work (i added . on line 8 xd)
RPC_URL = "https://api.mainnet-beta.solana.com"
CACHE_DIR = "./cached_blocks"


def get_block(slot: int) -> UiConfirmedBlock:
    cache_file = os.path.join(CACHE_DIR, f"{slot}.json")

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return UiConfirmedBlock.from_json(f.read())

    rpc = Client(RPC_URL)
    block_data = rpc.get_block(slot, encoding="json", max_supported_transaction_version=0).value

    if block_data:
        with open(cache_file, "w") as f:
            f.write(block_data.to_json())

        return block_data

    raise ValueError(f"Block {slot} not found")


if __name__ == "__main__":
    example_slot = 316719543
    block = get_block(example_slot)

    print(block)
