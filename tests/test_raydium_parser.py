import base64
import struct

from unittest.mock import MagicMock

import base58
import pytest

from raydium_parser.raydium_parser import RaydiumSwap, parse_block


@pytest.fixture
def mock_transaction():
    """Fixture to create a mock transaction with default attributes."""
    transaction = MagicMock()
    transaction.meta = MagicMock()
    transaction.meta.err = None
    transaction.meta.log_messages = []
    transaction.transaction.signatures = [MagicMock()]
    return transaction


def test_parse_block_with_no_transactions():
    """Test that parse_block raises a ValueError when no transactions are available."""
    mock_block = MagicMock()
    mock_block.transactions = None
    with pytest.raises(ValueError, match="Transactions are not available"):
        list(parse_block(mock_block, slot=123))


def test_parse_block_with_empty_logs(mock_transaction):
    """Test parse_block with a transaction that has no log messages."""
    mock_block = MagicMock()
    mock_block.transactions = [mock_transaction]
    result = list(parse_block(mock_block, slot=123))
    assert result == []


def test_parse_block_with_non_matching_log(mock_transaction):
    """Test parse_block with a log message that does not match the Raydium pattern."""
    mock_transaction.meta.log_messages = ["Unrelated log message"]
    mock_block = MagicMock()
    mock_block.transactions = [mock_transaction]
    result = list(parse_block(mock_block, slot=123))
    assert result == []


#Used for handilng the signature
class BytesMagicMock(MagicMock):
    def __bytes__(self):
        return self._mock_bytes

def test_parse_block_with_mock_data():
    """Test parse_block with a mock block containing a Raydium swap transaction."""
    # Create example binary data matching the RaydiumSwap structure
    example_data = struct.pack(
        "<IIIIIIIIII",
        2125473027,  # index_in_slot
        4484,        # index_in_tx
        0,           # mint_in
        0,           # mint_out
        256,         # amount_in
        0,           # amount_out
        2125473024,  # limit_amount
        1,           # limit_side (1 for 'mint_out')
        2946125824,  # post_pool_balance_mint_in
        9643         # post_pool_balance_mint_out
    )
    base64_data = base64.b64encode(example_data).decode("utf-8")

    # Create a mock transaction meta with the log message
    mock_meta = MagicMock()
    mock_meta.log_messages = [f"ray_log: {base64_data}"]
    mock_meta.err = None

    # Mock the signature object using the BytesMagicMock subclass
    mock_signature = BytesMagicMock()
    mock_signature._mock_bytes = base58.b58decode(
        "5KnpccMR2PcSBQrbWkX7UE5JUKc1ARZN1FSX8STgQBTp9LsCJrUqmTZrJUpYvatxDNbbf7Z5D2xNkthvdB5uGy3a"
    )

    # Create a mock transaction
    mock_transaction = MagicMock()
    mock_transaction.meta = mock_meta
    mock_transaction.transaction.signatures = [mock_signature]

    # Create a mock block containing the mock transaction
    mock_block = MagicMock()
    mock_block.transactions = [mock_transaction]

    # Expected RaydiumSwap instance
    expected_swap = RaydiumSwap(
        slot=316719543,
        index_in_slot=2125473027,
        index_in_tx=4484,
        signature="5KnpccMR2PcSBQrbWkX7UE5JUKc1ARZN1FSX8STgQBTp9LsCJrUqmTZrJUpYvatxDNbbf7Z5D2xNkthvdB5uGy3a",
        was_successful=True,
        mint_in=0,
        mint_out=0,
        amount_in=256,
        amount_out=0,
        limit_amount=2125473024,
        limit_side="mint_out",
        post_pool_balance_mint_in=2946125824,
        post_pool_balance_mint_out=9643
    )

    # Call the function under test
    result = list(parse_block(mock_block, slot=316719543))

    # Assertions
    assert len(result) == 1
    assert result[0] == expected_swap
