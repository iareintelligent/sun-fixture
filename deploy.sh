#!/bin/bash

# Celestial Lighting System Deployment Script
# Deploys AppDaemon app to Home Assistant via Samba or SSH

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration (can be overridden by environment variables or .env file)
HA_HOST="${HA_HOST:-homeassistant.local}"
HA_USER="${HA_USER:-root}"
HA_SAMBA_SHARE="${HA_SAMBA_SHARE:-/Volumes/config}"  # macOS Samba mount point
HA_SSH_PATH="${HA_SSH_PATH:-/config}"
DEPLOY_METHOD="${DEPLOY_METHOD:-samba}"  # Options: samba, ssh, local

# Load .env file if it exists
if [ -f .env ]; then
    echo -e "${BLUE}Loading configuration from .env file...${NC}"
    export $(cat .env | grep -E '^(HA_HOST|HA_USER|HA_SAMBA_SHARE|HA_SSH_PATH|DEPLOY_METHOD)=' | xargs)
fi

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if AppDaemon folder exists
check_appdaemon_exists() {
    local path="$1"
    if [ "$DEPLOY_METHOD" = "ssh" ]; then
        ssh "${HA_USER}@${HA_HOST}" "[ -d ${path}/appdaemon ]" 2>/dev/null
        return $?
    else
        [ -d "${path}/appdaemon" ]
        return $?
    fi
}

# Function to create backup
create_backup() {
    local target_path="$1"
    local backup_name="appdaemon_backup_$(date +%Y%m%d_%H%M%S)"
    
    print_info "Creating backup of existing AppDaemon configuration..."
    
    if [ "$DEPLOY_METHOD" = "ssh" ]; then
        ssh "${HA_USER}@${HA_HOST}" "cd ${target_path} && [ -d appdaemon/apps ] && cp -r appdaemon/apps /tmp/${backup_name}" 2>/dev/null || true
        if [ $? -eq 0 ]; then
            print_success "Backup created: /tmp/${backup_name}"
        fi
    else
        if [ -d "${target_path}/appdaemon/apps" ]; then
            cp -r "${target_path}/appdaemon/apps" "/tmp/${backup_name}" 2>/dev/null || true
            print_success "Backup created: /tmp/${backup_name}"
        fi
    fi
}

# Function to deploy via Samba
deploy_samba() {
    print_info "Deploying via Samba to ${HA_SAMBA_SHARE}..."
    
    # Check if Samba share is mounted
    if [ ! -d "$HA_SAMBA_SHARE" ]; then
        print_error "Samba share not mounted at ${HA_SAMBA_SHARE}"
        print_info "To mount on macOS: Finder → Go → Connect to Server → smb://${HA_HOST}/config"
        print_info "To mount on Linux: sudo mount -t cifs //${HA_HOST}/config ${HA_SAMBA_SHARE}"
        exit 1
    fi
    
    # Create AppDaemon directories if they don't exist
    mkdir -p "${HA_SAMBA_SHARE}/appdaemon/apps"
    mkdir -p "${HA_SAMBA_SHARE}/appdaemon/logs"
    
    # Create backup
    create_backup "$HA_SAMBA_SHARE"
    
    # Copy files
    print_info "Copying celestial.py..."
    cp appdaemon/apps/celestial.py "${HA_SAMBA_SHARE}/appdaemon/apps/"
    
    print_info "Copying apps.yaml..."
    cp appdaemon/apps/apps.yaml "${HA_SAMBA_SHARE}/appdaemon/apps/"
    
    print_success "Files deployed successfully via Samba!"
}

# Function to deploy via SSH
deploy_ssh() {
    print_info "Deploying via SSH to ${HA_USER}@${HA_HOST}..."
    
    # Test SSH connection
    if ! ssh -o ConnectTimeout=5 "${HA_USER}@${HA_HOST}" "echo 'SSH connection successful'" &>/dev/null; then
        print_error "Cannot connect to ${HA_USER}@${HA_HOST}"
        print_info "Make sure SSH is enabled in Home Assistant:"
        print_info "  1. Install 'SSH & Web Terminal' add-on"
        print_info "  2. Start the add-on and check 'Show in sidebar'"
        print_info "  3. Set up SSH keys or password authentication"
        exit 1
    fi
    
    # Create AppDaemon directories in BOTH locations
    ssh "${HA_USER}@${HA_HOST}" "mkdir -p ${HA_SSH_PATH}/appdaemon/apps ${HA_SSH_PATH}/appdaemon/logs"
    ssh "${HA_USER}@${HA_HOST}" "mkdir -p /addon_configs/a0d7b954_appdaemon/apps /addon_configs/a0d7b954_appdaemon/logs"
    
    # Create backup
    create_backup "/addon_configs/a0d7b954_appdaemon"
    
    # Copy files to addon_configs directory (the actual working directory)
    print_info "Copying celestial.py to addon directory..."
    scp appdaemon/apps/celestial.py "${HA_USER}@${HA_HOST}:/addon_configs/a0d7b954_appdaemon/apps/"
    
    print_info "Copying apps.yaml to addon directory..."
    scp appdaemon/apps/apps.yaml "${HA_USER}@${HA_HOST}:/addon_configs/a0d7b954_appdaemon/apps/"
    
    # Also copy to /config/apps for compatibility
    print_info "Copying to /config/apps for compatibility..."
    scp appdaemon/apps/celestial.py "${HA_USER}@${HA_HOST}:${HA_SSH_PATH}/apps/"
    scp appdaemon/apps/apps.yaml "${HA_USER}@${HA_HOST}:${HA_SSH_PATH}/apps/"
    
    print_success "Files deployed successfully via SSH!"
}

# Function to deploy locally (for testing)
deploy_local() {
    local target="${HA_LOCAL_PATH:-./test_deploy}"
    print_info "Deploying locally to ${target}..."
    
    # Create directories
    mkdir -p "${target}/appdaemon/apps"
    mkdir -p "${target}/appdaemon/logs"
    
    # Create backup
    create_backup "$target"
    
    # Copy files
    cp appdaemon/apps/celestial.py "${target}/appdaemon/apps/"
    cp appdaemon/apps/apps.yaml "${target}/appdaemon/apps/"
    
    print_success "Files deployed locally to ${target}!"
}

# Function to verify deployment
verify_deployment() {
    print_info "Verifying deployment..."
    
    local files_to_check=(
        "appdaemon/apps/celestial.py"
        "appdaemon/apps/apps.yaml"
    )
    
    local all_good=true
    
    for file in "${files_to_check[@]}"; do
        if [ "$DEPLOY_METHOD" = "ssh" ]; then
            if ssh "${HA_USER}@${HA_HOST}" "[ -f ${HA_SSH_PATH}/${file} ]" 2>/dev/null; then
                print_success "${file} exists"
            else
                print_error "${file} not found"
                all_good=false
            fi
        elif [ "$DEPLOY_METHOD" = "samba" ]; then
            if [ -f "${HA_SAMBA_SHARE}/${file}" ]; then
                print_success "${file} exists"
            else
                print_error "${file} not found"
                all_good=false
            fi
        fi
    done
    
    if $all_good; then
        print_success "All files deployed successfully!"
    else
        print_error "Some files are missing. Please check the deployment."
        exit 1
    fi
}

# Function to restart AppDaemon
restart_appdaemon() {
    print_info "Restarting AppDaemon..."
    
    if [ "$DEPLOY_METHOD" = "ssh" ]; then
        # Try to restart via Home Assistant CLI
        if ssh "${HA_USER}@${HA_HOST}" "ha addons restart a0d7b954_appdaemon" 2>/dev/null; then
            print_success "AppDaemon restarted successfully"
        else
            print_warning "Could not restart AppDaemon automatically. Please restart manually from HA UI."
        fi
    else
        print_info "Please restart AppDaemon from Home Assistant UI:"
        print_info "  Settings → Add-ons → AppDaemon → Restart"
    fi
}

# Function to tail logs
tail_logs() {
    print_info "Tailing AppDaemon logs (Ctrl+C to stop)..."
    
    if [ "$DEPLOY_METHOD" = "ssh" ]; then
        ssh "${HA_USER}@${HA_HOST}" "tail -f ${HA_SSH_PATH}/appdaemon/logs/appdaemon.log"
    elif [ "$DEPLOY_METHOD" = "samba" ]; then
        if [ -f "${HA_SAMBA_SHARE}/appdaemon/logs/appdaemon.log" ]; then
            tail -f "${HA_SAMBA_SHARE}/appdaemon/logs/appdaemon.log"
        else
            print_warning "Log file not found. AppDaemon may not be running yet."
        fi
    fi
}

# Main script
main() {
    echo "================================================"
    echo "   Celestial Lighting System Deployment"
    echo "================================================"
    echo ""
    print_info "Deployment method: ${DEPLOY_METHOD}"
    print_info "Target: ${HA_HOST}"
    echo ""
    
    # Check for required files
    if [ ! -f "appdaemon/apps/celestial.py" ]; then
        print_error "celestial.py not found. Are you in the project root directory?"
        exit 1
    fi
    
    if [ ! -f "appdaemon/apps/apps.yaml" ]; then
        print_error "apps.yaml not found. Are you in the project root directory?"
        exit 1
    fi
    
    # Deploy based on method
    case "$DEPLOY_METHOD" in
        samba)
            deploy_samba
            ;;
        ssh)
            deploy_ssh
            ;;
        local)
            deploy_local
            ;;
        *)
            print_error "Unknown deployment method: ${DEPLOY_METHOD}"
            print_info "Valid options: samba, ssh, local"
            exit 1
            ;;
    esac
    
    # Verify deployment
    verify_deployment
    
    # Optional: restart AppDaemon
    read -p "Do you want to restart AppDaemon? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        restart_appdaemon
    fi
    
    # Optional: tail logs
    read -p "Do you want to tail the AppDaemon logs? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tail_logs
    fi
    
    echo ""
    echo "================================================"
    print_success "Deployment complete!"
    echo ""
    print_info "Next steps:"
    print_info "  1. Check AppDaemon logs for any errors"
    print_info "  2. Verify lights are responding correctly"
    print_info "  3. Test Aurora dimmer click/rotate functions"
    echo "================================================"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --method)
            DEPLOY_METHOD="$2"
            shift 2
            ;;
        --host)
            HA_HOST="$2"
            shift 2
            ;;
        --user)
            HA_USER="$2"
            shift 2
            ;;
        --logs)
            tail_logs
            exit 0
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --method METHOD   Deployment method (samba, ssh, local)"
            echo "  --host HOST       Home Assistant host"
            echo "  --user USER       SSH username"
            echo "  --logs            Tail AppDaemon logs"
            echo "  --help            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  HA_HOST           Home Assistant host (default: homeassistant.local)"
            echo "  HA_USER           SSH username (default: root)"
            echo "  HA_SAMBA_SHARE    Samba mount point (default: /Volumes/config)"
            echo "  HA_SSH_PATH       SSH target path (default: /config)"
            echo "  DEPLOY_METHOD     Deployment method (default: samba)"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main