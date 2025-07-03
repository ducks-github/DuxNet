# DuxOS Airdrop Service

## Goal
The Airdrop Service distributes accumulated community funds to active, verified nodes on the Dux OS network, incentivizing participation and honest computation.

## Architecture Outline
- **Airdrop Manager**: Monitors the community fund balance and triggers airdrops when thresholds are met.
- **Eligibility Verifier**: Checks node activity and proof-of-computation to determine airdrop recipients.
- **Distribution Engine**: Executes Flop Coin transfers to eligible nodes using the Wallet API.
- **APIs**:
  - Community Fund API: To monitor and access funds
  - Node Registry API: To verify node status and eligibility
- **Scheduler**: Periodically checks for airdrop conditions and initiates distribution.
- **Logging & Auditing**: Records all airdrop events for transparency and verification.

## Data Flow
1. Community fund reaches threshold (e.g., 100 Flop Coin).
2. Eligibility Verifier compiles list of active nodes.
3. Distribution Engine sends airdrop payments to eligible nodes.
4. All events are logged for audit and transparency. 