#!/bin/bash
# Backup journal.db daily, keep 14 days
DB="/home/datnm/projects/trading/data/journal.db"
BACKUP_DIR="/home/datnm/projects/trading/data/journal_backups"
DATE=$(date +%Y%m%d_%H%M%S)

if [ -f "$DB" ]; then
    cp "$DB" "$BACKUP_DIR/journal_${DATE}.db"
    # Compress
    gzip -f "$BACKUP_DIR/journal_${DATE}.db"
    # Keep only last 14 backups
    ls -t "$BACKUP_DIR"/journal_*.db.gz | tail -n +15 | xargs -r rm -f
fi
