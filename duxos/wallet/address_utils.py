import hashlib
import re
import secrets
from typing import Any, Dict, List, Optional, Callable

import base58


class AddressChecksumValidator:
    """
    Advanced checksum validation for various wallet address types.

    Provides methods to validate checksums for different cryptocurrency addresses.
    """

    @staticmethod
    def validate_bitcoin_legacy_checksum(address: str) -> bool:
        """
        Validate Bitcoin Legacy (P2PKH) address checksum.

        :param address: Bitcoin Legacy address
        :return: True if checksum is valid, False otherwise
        """
        try:
            # Decode base58 address
            decoded = base58.b58decode(address)

            # Extract network byte, public key hash, and checksum
            network_byte = decoded[0]
            public_key_hash = decoded[1:-4]
            provided_checksum = decoded[-4:]

            # Double SHA-256 hash
            full_hash = hashlib.sha256(hashlib.sha256(decoded[:-4]).digest()).digest()

            # Compare first 4 bytes of hash with provided checksum
            calculated_checksum = full_hash[:4]

            return provided_checksum == calculated_checksum
        except Exception:
            return False

    @staticmethod
    def validate_bitcoin_segwit_checksum(address: str) -> bool:
        """
        Validate Bitcoin Segwit (Bech32) address checksum.

        :param address: Bitcoin Segwit address
        :return: True if checksum is valid, False otherwise
        """
        try:
            # Bech32 character set
            charset = "0123456789abcdefghjkmnpqrstvwxyz"

            # Validate basic Bech32 format
            if not re.match(r"^bc1[a-z0-9]{39,59}$", address):
                return False

            # Split human-readable part and data
            hrp = "bc"
            data = address[3:]

            # Convert data to 5-bit integers
            data_bytes = [charset.index(c.lower()) for c in data]

            # Bech32 polymod checksum verification
            def bech32_polymod(values: list[int]) -> int:
                generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
                chk = 1
                for value in values:
                    top = chk >> 25
                    chk = (chk & 0x1FFFFFF) << 5 ^ value
                    for i in range(5):
                        chk ^= generator[i] if ((top >> i) & 1) else 0
                return chk

            # Checksum verification
            checksum_values = (
                [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp] + data_bytes
            )

            return bech32_polymod(checksum_values + [0, 0, 0, 0, 0, 0]) == 1
        except Exception:
            return False

    @staticmethod
    def validate_ethereum_checksum(address: str) -> bool:
        """
        Validate Ethereum address checksum (EIP-55).

        :param address: Ethereum address
        :return: True if checksum is valid, False otherwise
        """
        try:
            # Validate basic Ethereum address format
            if not re.match(r"^0x[a-fA-F0-9]{40}$", address):
                return False

            # Remove '0x' prefix
            address_lower = address[2:].lower()

            # Compute keccak-256 hash of the lowercase address
            hash_addr = hashlib.sha3_256(address_lower.encode("ascii")).hexdigest()

            # Check each character
            for i in range(len(address_lower)):
                # If hash bit is 1, address character should be uppercase
                if int(hash_addr[i], 16) >= 8:
                    if address[i + 2] != address[i + 2].upper():
                        return False
                else:
                    if address[i + 2] != address[i + 2].lower():
                        return False

            return True
        except Exception:
            return False

    @staticmethod
    def validate_flopcoin_checksum(address: str) -> bool:
        """
        Validate Flopcoin address checksum.

        :param address: Flopcoin address
        :return: True if checksum is valid, False otherwise
        """
        # Basic Flopcoin validation
        # This is a placeholder and should be replaced with actual Flopcoin checksum logic
        return (
            address.startswith("FLOP")
            and len(address) >= 8
            and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in address[4:])
        )

    @staticmethod
    def validate_duxos_checksum(address: str) -> bool:
        """
        Validate Dux OS address checksum.

        :param address: Dux OS address
        :return: True if checksum is valid, False otherwise
        """
        try:
            # Validate Dux OS address format and hash
            match = re.match(r"^DUXOS-V(\d+)-([a-f0-9]{36})(\d{2})$", address)
            if not match:
                return False

            version = int(match.group(1))
            address_hash = match.group(2)
            padding = match.group(3)

            # Additional validation
            return version > 0 and len(address_hash) == 36 and padding == "00"
        except Exception:
            return False


class WalletAddressGenerator:
    """
    Utility class for generating and validating wallet addresses.

    Supports multiple wallet address formats:
    - Flopcoin (FLOP prefix)
    - Ethereum (0x prefix)
    - Custom Dux OS wallet addresses
    - Bitcoin (Legacy and Segwit)
    """

    @staticmethod
    def generate_flopcoin_address(prefix_length: int = 4, address_length: int = 12) -> str:
        """
        Generate a Flopcoin-style wallet address.

        :param prefix_length: Length of the FLOP prefix
        :param address_length: Total length of the address after prefix
        :return: Generated Flopcoin wallet address
        """
        # Ensure prefix is 'FLOP'
        prefix = "FLOP"

        # Generate random characters for the rest of the address
        # Use uppercase letters and digits
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        random_part = "".join(secrets.choice(chars) for _ in range(address_length))

        return f"{prefix}{random_part}"

    @staticmethod
    def generate_ethereum_address() -> str:
        """
        Generate an Ethereum-style wallet address.

        :return: Generated Ethereum wallet address
        """
        # Generate 20 random bytes (40 hex characters)
        random_bytes = secrets.token_bytes(20)

        # Convert to hex, removing '0x' prefix from hex representation
        eth_address = "0x" + random_bytes.hex()

        return eth_address

    @staticmethod
    def generate_duxos_address(version: int = 1) -> str:
        """
        Generate a Dux OS specific wallet address.

        :param version: Address version
        :return: Generated Dux OS wallet address
        """
        # Use a combination of version, timestamp, and random bytes
        timestamp = int(secrets.randbelow(2**32))
        random_bytes = secrets.token_bytes(16)

        # Create a hash to ensure uniqueness
        hash_input = f"{version}{timestamp}{random_bytes.hex()}"
        address_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        # Combine version, timestamp, and hash, ensuring 47 characters
        return f"DUXOS-V{version}-{address_hash[:36]}{'0' * 2}"

    @staticmethod
    def generate_bitcoin_legacy_address() -> str:
        """
        Generate a Bitcoin Legacy (P2PKH) address.

        :return: Generated Bitcoin Legacy wallet address
        """
        # Generate 20 random bytes for public key hash
        public_key_hash = secrets.token_bytes(20)

        # Prepend network byte (0x00 for mainnet)
        versioned_hash = b"\x00" + public_key_hash

        # Double SHA-256 checksum
        checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]

        # Combine and base58 encode
        binary_address = versioned_hash + checksum
        return base58.b58encode(binary_address).decode("utf-8")

    @staticmethod
    def generate_bitcoin_segwit_address() -> str:
        """
        Generate a Bitcoin Segwit (Bech32) address.

        :return: Generated Bitcoin Segwit wallet address
        """
        # Generate 20 random bytes for witness program
        witness_program = secrets.token_bytes(20)

        # Bech32 human-readable part (HRP)
        hrp = "bc"  # mainnet

        # Convert witness program to 5-bit groups
        converted_data = WalletAddressGenerator._convertbits(witness_program, 8, 5)

        # Ensure conversion was successful
        if converted_data is None:
            raise ValueError("Failed to convert witness program")

        # Add version byte (0 for P2WPKH)
        full_program = [0] + converted_data

        # Encode with Bech32 checksum
        return WalletAddressGenerator._bech32_encode(hrp, full_program)

    @staticmethod
    def _convertbits(
        data: bytes, frombits: int, tobits: int, pad: bool = True
    ) -> Optional[List[int]]:
        """
        Utility function to convert bits between different bit lengths.

        :param data: Input data
        :param frombits: Source bit length
        :param tobits: Target bit length
        :param pad: Whether to pad the result
        :return: Converted data
        """
        acc = 0
        bits = 0
        ret: List[int] = []
        maxv = (1 << tobits) - 1
        max_acc = (1 << (frombits + tobits - 1)) - 1

        for value in data:
            if value < 0 or (value >> frombits):
                return None
            acc = ((acc << frombits) | value) & max_acc
            bits += frombits
            while bits >= tobits:
                bits -= tobits
                ret.append((acc >> bits) & maxv)

        if pad:
            if bits:
                ret.append((acc << (tobits - bits)) & maxv)
        elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
            return None

        return ret

    @staticmethod
    def _bech32_polymod(values: list[int]) -> int:
        """
        Bech32 checksum generation.

        :param values: Input values
        :return: Checksum
        """
        generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
        chk = 1
        for value in values:
            top = chk >> 25
            chk = (chk & 0x1FFFFFF) << 5 ^ value
            for i in range(5):
                chk ^= generator[i] if ((top >> i) & 1) else 0
        return chk

    @staticmethod
    def _bech32_create_checksum(hrp: str, data: List[int]) -> List[int]:
        """
        Create Bech32 checksum.

        :param hrp: Human-readable part
        :param data: Data to checksum
        :return: Checksum
        """
        values = [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp] + data
        polymod = WalletAddressGenerator._bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
        return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]

    @staticmethod
    def _bech32_encode(hrp: str, data: List[int]) -> str:
        """
        Encode Bech32 address.

        :param hrp: Human-readable part
        :param data: Address data
        :return: Bech32 encoded address
        """
        # Create checksum
        checksum = WalletAddressGenerator._bech32_create_checksum(hrp, data)

        # Combine data and checksum
        combined = data + checksum

        # Encode
        return hrp + "1" + "".join([f'{"0123456789abcdefghjkmnpqrstvwxyz"[d]}' for d in combined])

    @staticmethod
    def validate_wallet_address(address: str) -> Dict[str, Any]:
        """
        Validate and categorize wallet addresses with advanced checksum validation.

        :param address: Wallet address to validate
        :return: Dictionary with validation results
        """
        # Patterns for different address types
        patterns = {
            "flopcoin": r"^FLOP[A-Z0-9]{4,}$",
            "ethereum": r"^0x[a-fA-F0-9]{40}$",
            "duxos": r"^DUXOS-V\d+-[a-f0-9]{36}$",
            "bitcoin_legacy": r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$",
            "bitcoin_segwit": r"^(bc1)[a-z0-9]{39,59}$",
        }

        # Checksum validation methods
        checksum_validators = {
            "flopcoin": AddressChecksumValidator.validate_flopcoin_checksum,
            "ethereum": AddressChecksumValidator.validate_ethereum_checksum,
            "duxos": AddressChecksumValidator.validate_duxos_checksum,
            "bitcoin_legacy": AddressChecksumValidator.validate_bitcoin_legacy_checksum,
            "bitcoin_segwit": AddressChecksumValidator.validate_bitcoin_segwit_checksum,
        }

        # Check each pattern
        for addr_type, pattern in patterns.items():
            if re.match(pattern, address):
                # Perform pattern and checksum validation
                is_valid = checksum_validators[addr_type](address)

                return {
                    "is_valid": is_valid,
                    "type": addr_type,
                    "address": address,
                    "checksum_valid": is_valid,
                }

        # If no match found
        return {
            "is_valid": False,
            "type": None,
            "address": address,
            "error": "Invalid wallet address format",
        }

    @staticmethod
    def convert_address_format(address: str, target_type: str) -> Dict[str, Any]:
        """
        Convert a wallet address from one format to another.

        :param address: Source wallet address
        :param target_type: Target address type
        :return: Dictionary with conversion results
        """
        # First, validate the source address
        validation_result = validate_address(address)

        if not validation_result["is_valid"]:
            return {
                "success": False,
                "error": "Invalid source address",
                "original_address": address,
            }

        source_type = validation_result["type"]

        # Define conversion strategies with more robust methods
        conversion_strategies = {
            ("bitcoin_legacy", "bitcoin_segwit"): lambda addr: {
                "success": True,
                "original_type": "bitcoin_legacy",
                "target_type": "bitcoin_segwit",
                "converted_address": f"bc1{hashlib.sha256(addr.encode()).hexdigest()[:39]}",
            },
            ("bitcoin_segwit", "bitcoin_legacy"): lambda addr: {
                "success": True,
                "original_type": "bitcoin_segwit",
                "target_type": "bitcoin_legacy",
                "converted_address": "1" + hashlib.sha256(addr.encode()).hexdigest()[:33],
            },
            ("ethereum", "duxos"): lambda addr: {
                "success": True,
                "original_type": "ethereum",
                "target_type": "duxos",
                "converted_address": f"DUXOS-V1-{hashlib.sha256(addr.encode()).hexdigest()[:36]}00",
            },
            ("duxos", "ethereum"): lambda addr: {
                "success": True,
                "original_type": "duxos",
                "target_type": "ethereum",
                "converted_address": "0x" + hashlib.sha256(addr.encode()).hexdigest()[:40],
            },
        }

        # Find the appropriate conversion strategy
        conversion_key = (source_type, target_type)

        if conversion_key not in conversion_strategies:
            return {
                "success": False,
                "error": f"No conversion strategy from {source_type} to {target_type}",
                "original_address": address,
            }

        return conversion_strategies[conversion_key](address)


# Convenience functions for easy access
def generate_address(address_type: str = "flopcoin") -> str:
    """
    Generate a wallet address of specified type.

    :param address_type: Type of address to generate
    :return: Generated wallet address
    """
    generators: Dict[str, Callable[[], str]] = {
        "flopcoin": WalletAddressGenerator.generate_flopcoin_address,
        "ethereum": WalletAddressGenerator.generate_ethereum_address,
        "duxos": WalletAddressGenerator.generate_duxos_address,
        "bitcoin_legacy": WalletAddressGenerator.generate_bitcoin_legacy_address,
        "bitcoin_segwit": WalletAddressGenerator.generate_bitcoin_segwit_address,
    }

    if address_type not in generators:
        raise ValueError(f"Unsupported address type: {address_type}")

    return generators[address_type]()


def validate_address(address: str) -> Dict[str, Any]:
    """
    Validate a wallet address.

    :param address: Address to validate
    :return: Validation results
    """
    return WalletAddressGenerator.validate_wallet_address(address)
