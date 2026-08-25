from __future__ import annotations

import unittest

from vera_mmu.addressing import AddressError, make_address, parse_address


class AddressTests(unittest.TestCase):
    """I009/I014/I015: the Core accepts only canonical, bounded VERA addresses."""

    def test_canonical_address_round_trip_with_escaping(self) -> None:
        address = make_address("demo-project", "knowledge", "decision alpha:1")
        self.assertEqual(address, "vera://demo-project/knowledge/decision%20alpha%3A1")
        parsed = parse_address(address)
        self.assertEqual(parsed.project_id, "demo-project")
        self.assertEqual(parsed.resource_type, "knowledge")
        self.assertEqual(parsed.identifier, "decision alpha:1")
        self.assertEqual(parsed.canonical, address)

    def test_rejects_unknown_resource_type(self) -> None:
        with self.assertRaises(AddressError):
            make_address("demo-project", "component", "core")

    def test_rejects_noncanonical_or_unsafe_address_forms(self) -> None:
        invalid_addresses = (
            "VERA://demo-project/knowledge/item",
            "vera://Demo-Project/knowledge/item",
            "vera://demo-project/unknown/item",
            "vera://demo-project/knowledge/..",
            "vera://demo-project/knowledge/%2E%2E",
            "vera://demo-project/knowledge/a%2Fb",
            "vera://demo-project/knowledge/item%7E",
            "vera://demo-project/knowledge",
        )
        for address in invalid_addresses:
            with self.subTest(address=address), self.assertRaises(AddressError):
                parse_address(address)

    def test_constructor_rejects_path_like_identifiers(self) -> None:
        for identifier in ("", ".", "..", "one/two", "one\\two", "\x00"):
            with self.subTest(identifier=identifier), self.assertRaises(AddressError):
                make_address("demo-project", "knowledge", identifier)


if __name__ == "__main__":
    unittest.main()
