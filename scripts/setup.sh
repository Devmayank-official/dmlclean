#!/usr/bin/env bash
# DMLClean Setup Script for Unix/Linux/macOS
# This script sets up the development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    log_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        log_error "Python 3.11 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    log_success "Python $PYTHON_VERSION found"
}

# Create virtual environment
create_venv() {
    log_info "Creating virtual environment..."
    
    if [ -d ".venv" ]; then
        log_warning "Virtual environment already exists. Removing..."
        rm -rf .venv
    fi
    
    python3 -m venv .venv
    log_success "Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    log_info "Activating virtual environment..."
    source .venv/bin/activate
    log_success "Virtual environment activated"
}

# Install dependencies
install_deps() {
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    log_info "Installing development dependencies..."
    pip install -e ".[dev]"
    
    log_success "Dependencies installed"
}

# Install pre-commit hooks
install_hooks() {
    log_info "Installing pre-commit hooks..."
    pre-commit install
    log_success "Pre-commit hooks installed"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    pytest tests/ -v --tb=short
    log_success "Tests passed"
}

# Main setup
main() {
    echo "========================================"
    echo "  DMLClean Setup Script"
    echo "========================================"
    echo ""
    
    check_python
    create_venv
    activate_venv
    install_deps
    install_hooks
    
    echo ""
    log_success "Setup complete!"
    echo ""
    echo "To get started:"
    echo "  1. Activate the virtual environment:"
    echo "     source .venv/bin/activate"
    echo ""
    echo "  2. Run DMLClean:"
    echo "     dmlclean --help"
    echo ""
    echo "  3. Run tests:"
    echo "     pytest tests/"
    echo ""
    echo "  4. Scan for cleanable files:"
    echo "     dmlclean scan"
    echo ""
}

# Run main function
main "$@"
