from lawu.attribute import Attribute, get_attribute_classes


def test_discovery():
    """Ensure our basic attribute discovery mechanism works."""
    attributes = get_attribute_classes()

    assert 'code' in attributes


def test_mandatory_properties():
    """Ensure necessary metadata is present on all attributes."""
    attributes = get_attribute_classes()

    for attr in attributes.values():
        assert attr.ADDED_IN is not None
        assert attr.MINIMUM_CLASS_VERSION is not None
