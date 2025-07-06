# DuxOS Escrow Governance System

## Overview

The DuxOS Escrow Governance System provides a decentralized governance mechanism for the escrow platform, allowing community members to propose, vote on, and execute changes to the system. This includes community fund allocations, escrow parameter changes, feature requests, and other governance decisions.

## Features

- **Proposal Creation**: Community members can create governance proposals
- **Voting System**: Weighted voting based on FLOP token holdings
- **Quorum Requirements**: Configurable minimum voting thresholds
- **Proposal Categories**: Organized proposal types (community fund, escrow params, etc.)
- **Execution System**: Automated execution of passed proposals
- **Audit Trail**: Complete history of proposals and votes

## Architecture

### Core Components

1. **GovernanceManager**: Business logic for proposal and voting management
2. **Proposal Model**: Database model for governance proposals
3. **Vote Model**: Database model for individual votes
4. **Governance API**: RESTful endpoints for governance operations

### Database Models

#### Proposal
```python
class Proposal(Base):
    id: str                    # Unique proposal ID
    title: str                 # Proposal title
    description: str           # Detailed description
    category: ProposalCategory # Proposal category
    status: ProposalStatus     # Current status
    proposer_wallet_id: int    # Wallet ID of proposer
    required_quorum: float     # Minimum voting power required
    voting_period_days: int    # Voting duration
    estimated_cost: float      # Estimated implementation cost
    funding_source: str        # Source of funding
    execution_data: dict       # Execution parameters
    created_at: datetime       # Creation timestamp
    voting_started_at: datetime # Voting start time
    voting_ends_at: datetime   # Voting end time
    executed_at: datetime      # Execution timestamp
```

#### Vote
```python
class Vote(Base):
    id: str                    # Unique vote ID
    proposal_id: str           # Associated proposal
    voter_wallet_id: int       # Voter's wallet ID
    vote_type: VoteType        # YES/NO/ABSTAIN
    voting_power: float        # Amount of FLOP used for voting
    reason: str                # Optional voting reason
    created_at: datetime       # Vote timestamp
```

### Proposal Categories

- `COMMUNITY_FUND`: Community fund allocation proposals
- `ESCROW_PARAMS`: Escrow system parameter changes
- `GOVERNANCE`: Governance system changes
- `FEATURE_REQUEST`: New feature proposals
- `BUG_FIX`: Bug fix proposals
- `OTHER`: Miscellaneous proposals

### Proposal Statuses

- `DRAFT`: Initial proposal state
- `ACTIVE`: Currently being voted on
- `PASSED`: Approved by community
- `REJECTED`: Rejected by community
- `EXPIRED`: Voting period expired without quorum
- `EXECUTED`: Successfully executed

## API Endpoints

### Proposal Management

#### Create Proposal
```http
POST /governance/proposals
Content-Type: application/json
X-API-Key: your-api-key

{
  "title": "Increase Community Fund Allocation",
  "description": "Proposal to increase community fund allocation from 5% to 7% of escrow amounts",
  "category": "community_fund",
  "proposer_wallet_id": 123,
  "required_quorum": 1000.0,
  "voting_period_days": 7,
  "estimated_cost": 0.0,
  "funding_source": "community_fund"
}
```

#### Get Proposals
```http
GET /governance/proposals
GET /governance/proposals?status=active
GET /governance/proposals?category=community_fund
```

#### Get Specific Proposal
```http
GET /governance/proposals/{proposal_id}
```

#### Activate Proposal
```http
POST /governance/proposals/{proposal_id}/activate
X-API-Key: your-api-key
```

### Voting

#### Cast Vote
```http
POST /governance/proposals/{proposal_id}/vote
Content-Type: application/json
X-API-Key: your-api-key

{
  "proposal_id": "proposal-123",
  "voter_wallet_id": 456,
  "vote_type": "yes",
  "voting_power": 100.0,
  "reason": "I support this proposal because it will benefit the community"
}
```

#### Get Vote Results
```http
GET /governance/proposals/{proposal_id}/results
```

#### Get Voter History
```http
GET /governance/votes/history/{voter_wallet_id}
```

#### Get Proposal Votes
```http
GET /governance/proposals/{proposal_id}/votes
```

### Proposal Lifecycle

#### Finalize Proposal
```http
POST /governance/proposals/{proposal_id}/finalize
X-API-Key: your-api-key
```

#### Execute Proposal
```http
POST /governance/proposals/{proposal_id}/execute?executor_wallet_id=789
X-API-Key: your-api-key
```

### Statistics

#### Get Governance Stats
```http
GET /governance/stats
```

Response:
```json
{
  "total_proposals": 25,
  "active_proposals": 3,
  "passed_proposals": 15,
  "executed_proposals": 12,
  "total_votes": 150,
  "total_voting_power": 5000.0
}
```

## Usage Examples

### Python Client Example

```python
import requests

# Configuration
API_BASE = "http://localhost:8000"
API_KEY = "supersecretapikey123"

headers = {"X-API-Key": API_KEY}

# Create a proposal
proposal_data = {
    "title": "Implement New Escrow Features",
    "description": "Add support for multi-party escrows and conditional releases",
    "category": "feature_request",
    "proposer_wallet_id": 123,
    "required_quorum": 500.0,
    "voting_period_days": 14,
    "estimated_cost": 1000.0,
    "funding_source": "community_fund"
}

response = requests.post(
    f"{API_BASE}/governance/proposals",
    json=proposal_data,
    headers=headers
)
proposal = response.json()
proposal_id = proposal["id"]

# Activate the proposal
requests.post(
    f"{API_BASE}/governance/proposals/{proposal_id}/activate",
    headers=headers
)

# Cast votes
vote_data = {
    "proposal_id": proposal_id,
    "voter_wallet_id": 456,
    "vote_type": "yes",
    "voting_power": 50.0,
    "reason": "This will improve the platform significantly"
}

requests.post(
    f"{API_BASE}/governance/proposals/{proposal_id}/vote",
    json=vote_data,
    headers=headers
)

# Check results
results = requests.get(f"{API_BASE}/governance/proposals/{proposal_id}/results").json()
print(f"Voting Results: {results}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8000';
const API_KEY = 'supersecretapikey123';

const headers = { 'X-API-Key': API_KEY };

// Create proposal
async function createProposal() {
    const proposalData = {
        title: 'Community Fund Airdrop',
        description: 'Distribute 1000 FLOP to active community members',
        category: 'community_fund',
        proposer_wallet_id: 123,
        required_quorum: 200.0,
        voting_period_days: 7,
        estimated_cost: 1000.0,
        funding_source: 'community_fund'
    };

    const response = await axios.post(
        `${API_BASE}/governance/proposals`,
        proposalData,
        { headers }
    );
    
    return response.data;
}

// Vote on proposal
async function voteOnProposal(proposalId, walletId, voteType, votingPower) {
    const voteData = {
        proposal_id: proposalId,
        voter_wallet_id: walletId,
        vote_type: voteType,
        voting_power: votingPower,
        reason: 'I support this initiative'
    };

    await axios.post(
        `${API_BASE}/governance/proposals/${proposalId}/vote`,
        voteData,
        { headers }
    );
}

// Get governance statistics
async function getStats() {
    const response = await axios.get(`${API_BASE}/governance/stats`);
    return response.data;
}
```

## Governance Process

### 1. Proposal Creation
- Community member creates a proposal with required details
- Proposal starts in `DRAFT` status
- System validates proposal parameters

### 2. Proposal Activation
- Proposal is activated for voting
- Voting period begins (configurable duration)
- Status changes to `ACTIVE`

### 3. Voting Period
- Community members cast votes using their FLOP tokens
- Each wallet can vote only once per proposal
- Voting power is based on FLOP token amount

### 4. Vote Calculation
- System calculates total voting power
- Determines if quorum is met
- Calculates vote percentages (YES/NO/ABSTAIN)

### 5. Proposal Finalization
- After voting period ends, proposal is finalized
- Status updated based on results:
  - `PASSED`: Quorum met and YES > NO
  - `REJECTED`: Quorum met and NO >= YES
  - `EXPIRED`: Quorum not met

### 6. Proposal Execution
- Passed proposals can be executed
- Execution parameters are processed
- Status changes to `EXECUTED`

## Security Features

### Rate Limiting
- 20 requests per 60 seconds per IP address
- Applied to all governance endpoints

### API Key Authentication
- Required for all write operations (POST/PUT)
- Static API key: `supersecretapikey123`

### Validation
- Proposal title: 5-200 characters
- Proposal description: 20-5000 characters
- Voting period: 1-30 days
- Required quorum: Positive value
- Voting power: Positive value

## Error Handling

### Common Error Codes

- `400 Bad Request`: Invalid proposal data or voting parameters
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Proposal not found
- `429 Too Many Requests`: Rate limit exceeded

### Error Response Format
```json
{
  "detail": "Error message describing the issue"
}
```

## Configuration

### Environment Variables
```bash
# API Configuration
GOVERNANCE_API_KEY=supersecretapikey123
GOVERNANCE_RATE_LIMIT=20
GOVERNANCE_RATE_PERIOD=60

# Database Configuration
DATABASE_URL=sqlite:///duxos_escrow.db
```

### Default Settings
- Voting period: 7 days
- Rate limit: 20 requests per minute
- Minimum title length: 5 characters
- Minimum description length: 20 characters
- Maximum voting period: 30 days

## Integration with Escrow System

The governance system integrates with the escrow system in several ways:

1. **Community Fund Proposals**: Can allocate funds from the community fund
2. **Escrow Parameter Changes**: Can modify escrow system parameters
3. **Feature Requests**: Can propose new escrow features
4. **Dispute Resolution**: Can propose changes to dispute resolution process

## Monitoring and Analytics

### Key Metrics
- Total proposals created
- Active proposals
- Passed vs rejected proposals
- Total voting participation
- Average voting power per proposal

### Dashboard Integration
The governance system provides endpoints for dashboard integration:
- Real-time proposal status
- Voting progress tracking
- Community participation metrics
- Historical governance data

## Future Enhancements

1. **Delegated Voting**: Allow token holders to delegate voting power
2. **Proposal Templates**: Pre-defined templates for common proposal types
3. **Multi-signature Execution**: Require multiple signatures for execution
4. **Proposal Discussion**: Built-in discussion forum for proposals
5. **Notification System**: Email/notification alerts for governance events
6. **Mobile App Support**: Native mobile app for governance participation

## Contributing

To contribute to the governance system:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For questions or support regarding the governance system:

- Check the API documentation
- Review the test examples
- Open an issue on the repository
- Contact the development team 