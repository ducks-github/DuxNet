# Build wallet-core

## Prerequisites
- CMake >= 3.18
- Clang
- Boost
- Protobuf
- Rust (for some features)
- Python (for bindings, optional)

## Build Instructions

```
cd external/wallet-core
./bootstrap.sh
cmake -Bbuild -H.
cmake --build build
```

For more details, see the official documentation: https://developer.trustwallet.com/wallet-core/building
