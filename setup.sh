#!/bin/bash

# DuxNet Setup Script
# This script automates the complete setup of DuxNet development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        REQUIRED_VERSION="3.8"
        
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $PYTHON_VERSION found (>= $REQUIRED_VERSION required)"
            return 0
        else
            print_error "Python $PYTHON_VERSION found, but $REQUIRED_VERSION or higher is required"
            return 1
        fi
    else
        print_error "Python 3 is not installed"
        return 1
    fi
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    if command_exists apt-get; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y python3-venv python3-pip python3-dev build-essential
    elif command_exists yum; then
        # CentOS/RHEL
        sudo yum install -y python3-devel python3-pip gcc
    elif command_exists brew; then
        # macOS
        brew install python3
    else
        print_warning "Could not detect package manager. Please install Python 3.8+ manually."
    fi
}

# Function to create virtual environment
create_virtual_environment() {
    print_status "Creating Python virtual environment..."
    
    if [ -d ".venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf .venv
    fi
    
    python3 -m venv .venv
    print_success "Virtual environment created successfully"
}

# Function to activate virtual environment
activate_virtual_environment() {
    print_status "Activating virtual environment..."
    source .venv/bin/activate
    
    # Verify activation
    if [[ "$VIRTUAL_ENV" == *".venv"* ]]; then
        print_success "Virtual environment activated"
        return 0
    else
        print_error "Failed to activate virtual environment"
        return 1
    fi
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        return 1
    fi
}

# Function to setup pre-commit hooks
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    
    if command_exists pre-commit; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "pre-commit not found. Installing..."
        pip install pre-commit
        pre-commit install
        print_success "Pre-commit hooks installed"
    fi
}

# Function to create default configuration files
create_default_configs() {
    print_status "Creating default configuration files..."
    
    # Create logs directory
    mkdir -p logs
    
    # Create default wallet config if it doesn't exist
    if [ ! -f "duxnet_wallet/config.yaml" ]; then
        cat > duxnet_wallet/config.yaml << EOF
rpc:
  host: "127.0.0.1"
  port: 32553
  user: "flopcoinrpc"
  password: "your_secure_password"

wallet:
  encryption: true
  backup_interval: 3600
  max_transaction_amount: 1000.0
  rate_limit_window: 3600
  max_transactions_per_window: 10
EOF
        print_success "Created default wallet configuration"
    fi
    
    # Create default store config if it doesn't exist
    if [ ! -f "duxnet_store/config.yaml" ]; then
        cat > duxnet_store/config.yaml << EOF
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_origins: ["*"]
  rate_limit_per_minute: 100

storage:
  path: "./store_metadata"
  use_ipfs: false
  backup_enabled: true
  backup_interval_hours: 24
  backup_retention_days: 7

rating:
  min_reviews_for_weighted: 5
  recency_weight_days: 30
  confidence_boost_factor: 0.2
  recency_boost_factor: 0.1

search:
  default_limit: 20
  max_limit: 100
  relevance_weights:
    name_match: 10.0
    description_match: 5.0
    tag_match: 3.0
    rating_boost: 0.5
    popularity_boost: 5.0

integration:
  task_engine_url: "http://localhost:8001"
  task_engine_timeout: 30
  wallet_url: "http://localhost:8002"
  wallet_timeout: 10
  registry_url: "http://localhost:8003"
  registry_timeout: 10
  escrow_url: "http://localhost:8004"
  escrow_timeout: 15

security:
  api_key_required: false
  rate_limiting_enabled: true
  content_validation: true
  max_file_size_mb: 10

logging:
  level: "INFO"
  file: "./logs/store.log"
  max_size_mb: 10
  backup_count: 5

performance:
  cache_enabled: true
  cache_ttl_seconds: 300
  max_connections: 100
  connection_timeout: 30
EOF
        print_success "Created default store configuration"
    fi
}

# Function to run basic tests
run_basic_tests() {
    print_status "Running basic tests..."
    
    # Test Python imports
    python3 -c "
import sys
sys.path.append('.')
try:
    from duxnet_store.store_service import StoreService
    from duxnet_wallet.wallet import FlopcoinWallet
    print('✓ Core modules import successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
"
    
    print_success "Basic tests passed"
}

# Function to display setup completion message
display_completion_message() {
    echo
    echo "=========================================="
    print_success "DuxNet setup completed successfully!"
    echo "=========================================="
    echo
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    echo "   source .venv/bin/activate"
    echo
    echo "2. Configure your wallet (edit duxnet_wallet/config.yaml):"
    echo "   - Set your Flopcoin RPC credentials"
    echo "   - Ensure Flopcoin Core is running"
    echo
    echo "3. Start the store service:"
    echo "   python3 -m duxnet_store.main --config duxnet_store/config.yaml"
    echo
    echo "4. For development, install pre-commit hooks:"
    echo "   pre-commit install"
    echo
    echo "Documentation:"
    echo "- README.md - Quickstart guide and overview"
    echo "- docs/api_reference.md - API documentation"
    echo "- docs/architecture.md - Technical architecture"
    echo
    echo "Happy coding! 🚀"
}

# Main setup function
main() {
    echo "=========================================="
    echo "DuxNet Development Environment Setup"
    echo "=========================================="
    echo
    
    # Check Python version
    if ! check_python_version; then
        print_status "Attempting to install system dependencies..."
        install_system_dependencies
        if ! check_python_version; then
            print_error "Python 3.8+ is required. Please install it manually."
            exit 1
        fi
    fi
    
    # Create virtual environment
    create_virtual_environment
    
    # Activate virtual environment
    if ! activate_virtual_environment; then
        print_error "Failed to activate virtual environment"
        exit 1
    fi
    
    # Install Python dependencies
    if ! install_python_dependencies; then
        print_error "Failed to install Python dependencies"
        exit 1
    fi
    
    # Setup pre-commit hooks (optional)
    if [ "$1" = "--with-pre-commit" ]; then
        setup_pre_commit
    fi
    
    # Create default configurations
    create_default_configs
    
    # Run basic tests
    run_basic_tests
    
    # Display completion message
    display_completion_message
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script is being executed
    main "$@"
else
    # Script is being sourced
    print_warning "This script should be executed, not sourced"
    print_status "Run: ./setup.sh"
fi 