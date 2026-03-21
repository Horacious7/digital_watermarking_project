import numpy as np
import pytest

import watermarking.embed as embed_module
import watermarking.extract as extract_module


def _resolve_pad_func(module):
    for name in ("pad_to_block", "_pad_to_block", "pad_image_to_block"):
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    raise AttributeError(f"No padding helper found in {module.__name__}")


embed_pad_to_block = _resolve_pad_func(embed_module)
extract_pad_to_block = _resolve_pad_func(extract_module)


@pytest.mark.parametrize("shape,block_size", [((15, 17), 8), ((8, 8), 8), ((1, 1), 8)])
def test_symmetric_padding_makes_shape_divisible_embed(shape, block_size):
    """
    Symmetric padding helper should produce dimensions divisible by block_size.
    Tests embed module implementation.
    """
    arr = np.arange(shape[0] * shape[1], dtype=np.float32).reshape(shape)
    padded, pad = embed_pad_to_block(arr, block_size)

    assert padded.shape[0] % block_size == 0
    assert padded.shape[1] % block_size == 0
    assert padded.shape[0] >= arr.shape[0]
    assert padded.shape[1] >= arr.shape[1]
    assert isinstance(pad, tuple) and len(pad) == 2


@pytest.mark.parametrize("shape,block_size", [((21, 10), 8), ((16, 24), 8), ((7, 9), 4)])
def test_symmetric_padding_makes_shape_divisible_extract(shape, block_size):
    """
    Symmetric padding helper should produce dimensions divisible by block_size.
    Tests extract module implementation.
    """
    arr = np.arange(shape[0] * shape[1], dtype=np.float32).reshape(shape)
    padded, pad = extract_pad_to_block(arr, block_size)

    assert padded.shape[0] % block_size == 0
    assert padded.shape[1] % block_size == 0
    assert padded.shape[0] >= arr.shape[0]
    assert padded.shape[1] >= arr.shape[1]
    assert isinstance(pad, tuple) and len(pad) == 2


def test_padding_no_change_when_already_divisible():
    """If shape is already divisible by block size, no padding should be added."""
    arr = np.ones((16, 24), dtype=np.float32)
    padded, pad = embed_pad_to_block(arr, 8)

    assert padded.shape == arr.shape
    assert pad == (0, 0)
