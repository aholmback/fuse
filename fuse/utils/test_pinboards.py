import pytest

@pytest.fixture
def pinboard():
    from fuse.utils import pinboards
    return pinboards.Pinboard()

def test_post_and_get_pin(pinboard):
    pinboard.post('test_pin', 'test_message')
    pin, = pinboard.get(exclude=[])

    assert pin.label == 'test_pin'
    assert pin.message == 'test_message'

def test_exclude_pins(pinboard):
    pinboard.post('test_pin_a', 'test_message_a')
    pinboard.post('test_pin_b', 'test_message_b')
    pinboard.post('test_pin_c', 'test_message_c')
    pinboard.post('test_pin_d', 'test_message_d')
    pinboard.post('test_pin_e', 'test_message_e')

    pin_b, pin_d = pinboard.get(exclude=[0,2,4])

    assert pin_b.label == 'test_pin_b'
    assert pin_b.message == 'test_message_b'

    assert pin_d.label == 'test_pin_d'
    assert pin_d.message == 'test_message_d'

