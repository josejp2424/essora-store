#!/bin/bash
# josejp2424
#
# Copyright (C) 2025 josejp2424
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Author: josejp2424
# Project: Essora Community

# Flatpak icons directory
ICON_BASE="/var/lib/flatpak/exports/share/icons"

# Output JSON file
OUTPUT_FILE="/usr/local/essora-store/icon-cache.json"

# Date tracking file
DATE_FILE="/usr/local/essora-store/last-update.txt"

# Create output directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Get current date (YYYY-MM-DD)
CURRENT_DATE=$(date +%Y-%m-%d)

# Check if we need to update
NEED_UPDATE=0

if [ -f "$DATE_FILE" ]; then
    LAST_UPDATE=$(cat "$DATE_FILE")
    if [ "$LAST_UPDATE" != "$CURRENT_DATE" ]; then
        NEED_UPDATE=1
        echo "Last update was on $LAST_UPDATE. Updating cache for today ($CURRENT_DATE)..."
    else
        echo "Cache already updated today ($CURRENT_DATE). Using existing cache."
    fi
else
    NEED_UPDATE=1
    echo "No previous update found. Creating cache for today ($CURRENT_DATE)..."
fi

# Only generate new cache if needed
if [ $NEED_UPDATE -eq 1 ]; then
    # Start JSON
    echo "{" > "$OUTPUT_FILE"

    # Function to find icons in all hicolor subdirectories
    find_icons() {
        local count=0
        local temp_file=$(mktemp)
        
        # Search in all icon sizes (16x16, 22x22, 24x24, 32x32, 48x48, 64x64, 128x128, scalable)
        for size_dir in "$ICON_BASE"/hicolor/*x* "$ICON_BASE"/hicolor/scalable; do
            if [ -d "$size_dir/apps" ]; then
                echo "Searching in: $size_dir/apps" >&2
                find "$size_dir/apps" -type f \( -name "*.svg" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.xpm" \) 2>/dev/null >> "$temp_file"
            fi
        done
        
        # Also search in /icons directly (some apps might put icons there)
        if [ -d "$ICON_BASE" ]; then
            find "$ICON_BASE" -type f \( -name "*.svg" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) 2>/dev/null | grep -v "hicolor" >> "$temp_file"
        fi
        
        # Remove duplicates and count
        if [ -s "$temp_file" ]; then
            sort -u "$temp_file" > "${temp_file}.uniq"
            total_files=$(wc -l < "${temp_file}.uniq")
            
            # Process each unique icon
            while read -r icon_path; do
                # Extract base name without extension
                icon_name=$(basename "$icon_path" | sed 's/\.[^.]*$//')
                # Clean name (remove special characters)
                icon_name=$(echo "$icon_name" | sed 's/[^a-zA-Z0-9._-]/_/g')
                
                ((count++))
                
                # Add to JSON (no comma on last element)
                if [ $count -eq $total_files ]; then
                    echo "  \"$icon_name\": \"$icon_path\"" >> "$OUTPUT_FILE"
                else
                    echo "  \"$icon_name\": \"$icon_path\"," >> "$OUTPUT_FILE"
                fi
            done < "${temp_file}.uniq"
            
            rm -f "$temp_file" "${temp_file}.uniq"
        else
            total_files=0
            rm -f "$temp_file"
        fi
        
        echo "$count"
    }

    # Find icons
    total_icons=$(find_icons)

    if [ "$total_icons" -eq 0 ]; then
        echo "  \"error\": \"No icons found in $ICON_BASE\"" >> "$OUTPUT_FILE"
        echo "  \"message\": \"Run 'flatpak update --appstream' to download icons\"" >> "$OUTPUT_FILE"
    fi

    # Close JSON
    echo "}" >> "$OUTPUT_FILE"

    # Save current date
    echo "$CURRENT_DATE" > "$DATE_FILE"

    echo "JSON created at: $OUTPUT_FILE"
    echo "Total icons processed: $total_icons"

    # Show some statistics if icons were found
    if [ "$total_icons" -gt 0 ]; then
        echo ""
        echo "Statistics:"
        echo "   - Total icons: $total_icons"
        echo "   - Base directory: $ICON_BASE"
        
        # Show some examples
        echo ""
        echo "First 5 icons found:"
        head -5 "$OUTPUT_FILE" | grep -v "{" | grep -v "}" | sed 's/^/   /'
    fi
else
    # Just show info about existing cache
    if [ -f "$OUTPUT_FILE" ]; then
        total_icons=$(grep -c ":" "$OUTPUT_FILE" 2>/dev/null || echo "0")
        echo "Using existing cache from $LAST_UPDATE"
        echo "Total icons in cache: $total_icons"
        echo "Cache location: $OUTPUT_FILE"
    else
        echo "Warning: Cache file not found but date file exists. This shouldn't happen."
    fi
fi
