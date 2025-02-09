import base64
import logging
import re
import struct

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

import base58 #I installed in through pip. Maybe this is a mistake but fuck it we ball

from solders.transaction_status import UiConfirmedBlock

from .rpc_utils import get_block

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RaydiumSwap:
    slot: int
    index_in_slot: int
    index_in_tx: int

    signature: str

    was_successful: bool

    mint_in: int
    mint_out: int
    amount_in: int
    amount_out: int

    limit_amount: int
    limit_side: Literal["mint_in", "mint_out"]

    post_pool_balance_mint_in: int
    post_pool_balance_mint_out: int


#No idea if this is a correct aproach xd
RAYDIUM_PROGRAM_ID = {
    "Legacy_AMM_v4": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
}


def parse_block(block: UiConfirmedBlock, slot: int) -> Iterator[RaydiumSwap]:
    if block.transactions is None:
        raise ValueError("Transactions are not available")

    #No idea if this is a correct aproach either (but it works {I think [kurwa nie wiem]}) xd
    raydium_swap_pattern = re.compile(r"ray_log: ([A-Za-z0-9+/=]+)")

    for transaction in block.transactions:
        meta = transaction.meta
        if meta is None or meta.err is not None or meta.log_messages is None:
            continue

        # Ignore vote transactions
        if any(msg.startswith("Program Vote111111111111111111111111111111111111111") for msg in meta.log_messages):
            continue

        # Find Raydium swap logs
        for log in meta.log_messages:
            match = raydium_swap_pattern.search(log)
            if match:
                base64_data = match.group(1)
                decoded_bytes = base64.b64decode(base64_data)

                try:
                    # Unpack binary data assuming 10 integers
                    unpacked_data = struct.unpack("<IIIIIIIIII", decoded_bytes[:40])

                    # Convert the signature object to a base58-encoded string
                    signature_obj = transaction.transaction.signatures[0]
                    signature_bytes = bytes(signature_obj)  # Convert to bytes
                    signature_str = base58.b58encode(signature_bytes).decode("utf-8")

                    yield RaydiumSwap(
                        slot=slot,
                        index_in_slot=unpacked_data[0],
                        index_in_tx=unpacked_data[1],
                        signature=signature_str,
                        was_successful=True, #We are checking it before 
                        mint_in=unpacked_data[2],
                        mint_out=unpacked_data[3],
                        amount_in=unpacked_data[4],
                        amount_out=unpacked_data[5],
                        limit_amount=unpacked_data[6],
                        limit_side="mint_in" if unpacked_data[7] == 0 else "mint_out",
                        post_pool_balance_mint_in=unpacked_data[8],
                        post_pool_balance_mint_out=unpacked_data[9],
                    )
                except struct.error:
                    continue  # Ignore parsing errors




if __name__ == "__main__":
    block = get_block(316719543)
    swaps = parse_block(block, 316719543)

    for swap in swaps:
        print(swap)
