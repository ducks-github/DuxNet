import re

import pytest

from duxos.wallet.address_utils import (
    AddressChecksumValidator,
    WalletAddressGenerator,
    generate_address,
    validate_address,
)


class TestWalletAddressGenerator:
    def test_generate_flopcoin_address(self):
        """Test Flopcoin address generation."""
        address = WalletAddressGenerator.generate_flopcoin_address()

        assert address.startswith("FLOP")
        assert len(address) >= 8  # FLOP + at least 4 chars
        assert re.match(r"^FLOP[A-Z0-9]+$", address)

    def test_generate_ethereum_address(self):
        """Test Ethereum address generation."""
        address = WalletAddressGenerator.generate_ethereum_address()

        assert address.startswith("0x")
        assert len(address) == 42  # 0x + 40 hex chars
        assert re.match(r"^0x[a-fA-F0-9]{40}$", address)

    def test_generate_duxos_address(self):
        """Test Dux OS address generation."""
        address = WalletAddressGenerator.generate_duxos_address()

        assert address.startswith("DUXOS-V")
        assert len(address) == 47  # DUXOS-V1- + 32 char hash
        assert re.match(r"^DUXOS-V\d+-[a-f0-9]{32}$", address)

    def test_validate_flopcoin_address(self):
        """Test Flopcoin address validation."""
        valid_addresses = ["FLOP12345ABCDE", "FLOP9999ZZZZ", "FLOPA1B2C3D4E5"]
        invalid_addresses = [
            "FLOP123",  # Too short
            "flop12345ABCDE",  # Lowercase not allowed
            "FLOP-12345",  # No special characters
            "0xABCDE12345",  # Wrong prefix
        ]

        for addr in valid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is True
            assert result["type"] == "flopcoin"

        for addr in invalid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is False

    def test_validate_ethereum_address(self):
        """Test Ethereum address validation."""
        valid_addresses = [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xABCDEF1234567890ABCDEF1234567890ABCDEF12",
        ]
        invalid_addresses = [
            "0x123",  # Too short
            "0xG234567890abcdef1234567890abcdef12345678",  # Invalid hex
            "FLOP12345ABCDE",  # Wrong prefix
            "1x1234567890abcdef1234567890abcdef12345678",  # Wrong prefix
        ]

        for addr in valid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is True
            assert result["type"] == "ethereum"

        for addr in invalid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is False

    def test_generate_address_function(self):
        """Test the generate_address convenience function."""
        # Test default (Flopcoin)
        addr = generate_address()
        assert addr.startswith("FLOP")

        # Test specific types
        flopcoin_addr = generate_address("flopcoin")
        assert flopcoin_addr.startswith("FLOP")

        ethereum_addr = generate_address("ethereum")
        assert ethereum_addr.startswith("0x")

        duxos_addr = generate_address("duxos")
        assert duxos_addr.startswith("DUXOS-V")

    def test_generate_address_invalid_type(self):
        """Test generating address with an invalid type."""
        with pytest.raises(ValueError):
            generate_address("invalid_type")

    def test_address_uniqueness(self):
        """Test that generated addresses are unique."""
        # Generate multiple addresses and ensure they're different
        flopcoin_addresses = {generate_address("flopcoin") for _ in range(100)}
        ethereum_addresses = {generate_address("ethereum") for _ in range(100)}
        duxos_addresses = {generate_address("duxos") for _ in range(100)}

        assert len(flopcoin_addresses) == 100
        assert len(ethereum_addresses) == 100
        assert len(duxos_addresses) == 100

    def test_generate_bitcoin_legacy_address(self):
        """Test Bitcoin Legacy (P2PKH) address generation."""
        address = WalletAddressGenerator.generate_bitcoin_legacy_address()

        assert address[0] in ["1", "3"]  # Valid Legacy address starts with 1 or 3
        assert len(address) >= 26  # Minimum length for Legacy address
        assert len(address) <= 35  # Maximum length for Legacy address
        assert re.match(r"^[13][a-km-zA-HJ-NP-Z1-9]+$", address)

    def test_generate_bitcoin_segwit_address(self):
        """Test Bitcoin Segwit (Bech32) address generation."""
        address = WalletAddressGenerator.generate_bitcoin_segwit_address()

        assert address.startswith("bc1")  # Mainnet Segwit addresses start with bc1
        assert len(address) >= 42  # Minimum length for Segwit address
        assert len(address) <= 62  # Maximum length for Segwit address
        assert re.match(r"^bc1[a-z0-9]+$", address)

    def test_validate_bitcoin_legacy_address(self):
        """Test Bitcoin Legacy address validation."""
        valid_addresses = [
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
            "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
            "12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX",
        ]
        invalid_addresses = [
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNV",  # Too short
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2X",  # Too long
            "0BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",  # Invalid first character
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",  # Segwit address
        ]

        for addr in valid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is True
            assert result["type"] == "bitcoin_legacy"

        for addr in invalid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is False

    def test_validate_bitcoin_segwit_address(self):
        """Test Bitcoin Segwit address validation."""
        valid_addresses = [
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
            "bc1qc7slrfxvslvayelx2ngsp4rg0skz3gn0glc7t7",
            "bc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qccfmv3",
        ]
        invalid_addresses = [
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5m",  # Too short
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",  # Legacy address
            "bc1Qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",  # Invalid case
        ]

        for addr in valid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is True
            assert result["type"] == "bitcoin_segwit"

        for addr in invalid_addresses:
            result = validate_address(addr)
            assert result["is_valid"] is False

    def test_address_conversion(self):
        """Test wallet address format conversion."""
        test_cases = [
            {
                "source_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
                "source_type": "bitcoin_legacy",
                "target_type": "bitcoin_segwit",
                "expected_prefix": "bc1",
            },
            {
                "source_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
                "source_type": "bitcoin_segwit",
                "target_type": "bitcoin_legacy",
                "expected_prefix": "1",
            },
            {
                "source_address": "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
                "source_type": "ethereum",
                "target_type": "duxos",
                "expected_prefix": "DUXOS-V1-",
            },
            {
                "source_address": "DUXOS-V1-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "source_type": "duxos",
                "target_type": "ethereum",
                "expected_prefix": "0x",
            },
        ]

        for case in test_cases:
            result = WalletAddressGenerator.convert_address_format(
                case["source_address"], case["target_type"]
            )

            assert result["success"] is True, f"Conversion failed for {case['source_address']}"
            assert result["original_type"] == case["source_type"], "Incorrect source type"
            assert result["target_type"] == case["target_type"], "Incorrect target type"
            assert result["converted_address"].startswith(
                case["expected_prefix"]
            ), "Incorrect address prefix"

    def test_address_conversion_invalid_source(self):
        """Test address conversion with an invalid source address."""
        invalid_address = "INVALID_ADDRESS"
        result = WalletAddressGenerator.convert_address_format(invalid_address, "ethereum")

        assert result["success"] is False
        assert result["error"] == "Invalid source address"
        assert result["original_address"] == invalid_address

    def test_address_conversion_unsupported_strategy(self):
        """Test address conversion with an unsupported conversion strategy."""
        valid_address = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        result = WalletAddressGenerator.convert_address_format(valid_address, "flopcoin")

        assert result["success"] is False
        assert "No conversion strategy" in result["error"]
        assert result["original_address"] == valid_address


class TestAddressChecksumValidator:
    def test_bitcoin_legacy_checksum(self):
        """Test Bitcoin Legacy address checksum validation."""
        valid_addresses = [
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",  # Valid checksum
            "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",  # Valid checksum
        ]
        invalid_addresses = [
            "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN3",  # Invalid checksum
            "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLx",  # Invalid checksum
        ]

        for addr in valid_addresses:
            assert AddressChecksumValidator.validate_bitcoin_legacy_checksum(addr) is True

        for addr in invalid_addresses:
            assert AddressChecksumValidator.validate_bitcoin_legacy_checksum(addr) is False

    def test_bitcoin_segwit_checksum(self):
        """Test Bitcoin Segwit address checksum validation."""
        valid_addresses = [
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
            "bc1qc7slrfxvslvayelx2ngsp4rg0skz3gn0glc7t7",
        ]
        invalid_addresses = [
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mda",  # Invalid checksum
            "bc1qc7slrfxvslvayelx2ngsp4rg0skz3gn0glc7t8",  # Invalid checksum
        ]

        for addr in valid_addresses:
            assert AddressChecksumValidator.validate_bitcoin_segwit_checksum(addr) is True

        for addr in invalid_addresses:
            assert AddressChecksumValidator.validate_bitcoin_segwit_checksum(addr) is False

    def test_ethereum_checksum(self):
        """Test Ethereum address checksum validation."""
        valid_addresses = [
            "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
            "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
        ]
        invalid_addresses = [
            "0x5aaeb6053F3E94C9b9A09f33669435E7Ef1BeAed",  # Invalid case
            "0xFB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",  # Invalid case
        ]

        for addr in valid_addresses:
            assert AddressChecksumValidator.validate_ethereum_checksum(addr) is True

        for addr in invalid_addresses:
            assert AddressChecksumValidator.validate_ethereum_checksum(addr) is False

    def test_duxos_checksum(self):
        """Test Dux OS address checksum validation."""
        valid_addresses = [
            "DUXOS-V1-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "DUXOS-V2-f0e9d8c7b6a5987654321fedcba098765",
        ]
        invalid_addresses = [
            "DUXOS-V0-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",  # Invalid version
            "DUXOS-V1-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5",  # Invalid hash length
            "DUXOS-V3-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q",  # Invalid format
        ]

        for addr in valid_addresses:
            assert AddressChecksumValidator.validate_duxos_checksum(addr) is True

        for addr in invalid_addresses:
            assert AddressChecksumValidator.validate_duxos_checksum(addr) is False

    def test_validate_address_with_checksum(self):
        """Test validate_address method with checksum validation."""
        test_cases = [
            # Valid addresses
            ("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", True),
            ("0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", True),
            ("DUXOS-V1-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6", True),
            # Invalid addresses
            ("1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN3", False),
            ("0x5aaeb6053F3E94C9b9A09f33669435E7Ef1BeAed", False),
            ("DUXOS-V0-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6", False),
        ]

        for address, expected_validity in test_cases:
            result = validate_address(address)
            assert result["is_valid"] == expected_validity
            assert result["checksum_valid"] == expected_validity
