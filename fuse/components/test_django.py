import pytest

@pytest.fixture
def instantiated():
    from fuse.components.django import Django
    from fuse.utils import prompts, validators, pinboards
    from fuse import models

    return Django(
        name='django',
        prompter=prompts.NullPrompt,
        prompts=models.Prompt,
        resources=models.Resource,
        validators=validators,
        pinboard=pinboards.Pinboard(),
    )

@pytest.fixture
def post_setup(instantiated):
    instantiated.setup()
    return instantiated

@pytest.fixture
def post_configure(post_setup):
    post_setup.configure()
    return post_setup

def test_init(instantiated):
    assert instantiated.name == 'django'

def test_setup(post_setup):
    pins = post_setup.pinboard.get(exclude=[])
    assert len(pins) == 3
