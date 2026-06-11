#!/bin/bash
# ============================================================
#  Paper Digest - Linux/Mac Cron Job Setup
#  设置每天 8:00 自动运行
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(which python3 || which python)"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"
LOG_FILE="$SCRIPT_DIR/logs/cron.log"
CRON_MARKER="# PAPER_DIGEST_CRON"

echo "🌱 Paper Digest - Cron Job Setup"
echo "========================================"
echo "  Python: $PYTHON"
echo "  Script: $MAIN_SCRIPT"
echo "  Log: $LOG_FILE"
echo "========================================"
echo ""

# Check for --remove flag
if [ "$1" = "--remove" ]; then
    echo "Removing cron job..."
    crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab -
    echo "✅ Cron job removed."
    exit 0
fi

# Get schedule time (default 08:00)
TIME="${1:-08:00}"
HOUR=$(echo "$TIME" | cut -d: -f1)
MINUTE=$(echo "$TIME" | cut -d: -f2)

# Ensure log directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Build cron entry
CRON_ENTRY="$MINUTE $HOUR * * * cd $SCRIPT_DIR && $PYTHON $MAIN_SCRIPT >> $LOG_FILE 2>&1 $CRON_MARKER"

# Remove old entry if exists
crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab -

# Add new entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job created successfully!"
echo "   Schedule: Every day at $HOUR:$MINUTE"
echo ""
echo "💡 Tips:"
echo "   - View all cron jobs: crontab -l"
echo "   - Edit cron jobs: crontab -e"
echo "   - Remove this job: ./setup_cron.sh --remove"
echo "   - Check logs: tail -f $LOG_FILE"
