#!/bin/bash
# check_albums_cache.sh - Script to analyze Spotify albums cache with jq
# Usage: ./check_albums_cache.sh [path/to/cache/file]

# Set default cache path based on typical locations
DEFAULT_CACHE_PATH="$HOME/.cache/spotify-tools/albums_cache.json"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it first."
    echo "  Ubuntu/Debian: sudo apt install jq"
    echo "  macOS: brew install jq"
    echo "  Fedora: sudo dnf install jq"
    exit 1
fi

# Get cache file path from argument or use default
CACHE_FILE=${1:-$DEFAULT_CACHE_PATH}

if [ ! -f "$CACHE_FILE" ]; then
    echo "Error: Cache file not found at $CACHE_FILE"
    exit 1
fi

echo "Analyzing Spotify albums cache: $CACHE_FILE"
echo "----------------------------------------"

# Check if the file is valid JSON
if ! jq empty "$CACHE_FILE" 2>/dev/null; then
    echo "Error: Invalid JSON in cache file."
    exit 1
fi

# Get cache timestamp and format it
TIMESTAMP=$(jq '.timestamp' "$CACHE_FILE")
if [ -n "$TIMESTAMP" ]; then
    DATE=$(date -r "$TIMESTAMP" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -d "@$TIMESTAMP" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)
    echo "Cache created: $DATE"
fi

echo "----------------------------------------"

# Count total albums (raw count from all years)
TOTAL_RAW=$(jq '[.albums_by_year | .[] | length] | add' "$CACHE_FILE")
echo "Total albums (sum of all years): $TOTAL_RAW"

# Count unique album URIs
UNIQUE_ALBUMS=$(jq '[.albums_by_year | .[] | .[].uri] | unique | length' "$CACHE_FILE")
echo "Unique albums (by URI): $UNIQUE_ALBUMS"

# Check for difference
if [ "$TOTAL_RAW" -ne "$UNIQUE_ALBUMS" ]; then
    echo "DISCREPANCY DETECTED: $((TOTAL_RAW - UNIQUE_ALBUMS)) albums appear in multiple years"
fi

echo "----------------------------------------"

# List years sorted by number of albums (descending)
echo "Top 10 years by album count:"
jq -r '.albums_by_year | to_entries | sort_by(.value | length) | reverse | .[0:10] | .[] | "\(.key): \(.value | length) albums"' "$CACHE_FILE"

echo "----------------------------------------"

# Check for duplicate albums (same URI in different years)
echo "Checking for duplicate albums across years..."
jq -r '
.albums_by_year as $years |
[
  $years | 
  to_entries[] |
  .key as $year |
  .value[] | 
  {year: $year, uri: .uri, name: .name, artists: .artists}
] |
group_by(.uri) |
map(select(length > 1)) |
.[] |
"Album \"\(.[0].name)\" by \(.[0].artists[0]) appears in \(length) different years: \(map(.year) | join(", "))"
' "$CACHE_FILE" > /tmp/duplicates.txt

DUPLICATE_COUNT=$(wc -l < /tmp/duplicates.txt | tr -d ' ')

if [ "$DUPLICATE_COUNT" -eq 0 ]; then
    echo "No duplicate albums found across years."
else
    echo "Found $DUPLICATE_COUNT albums that appear in multiple years:"
    cat /tmp/duplicates.txt | head -10  # Show first 10 duplicates
    
    if [ "$DUPLICATE_COUNT" -gt 10 ]; then
        echo "...and $((DUPLICATE_COUNT - 10)) more"
    fi
fi

echo "----------------------------------------"

# Show distribution of albums by decade
echo "Albums by decade:"
jq -r '
.albums_by_year | 
to_entries | 
map({decade: (.key[0:3] + "0s"), count: (.value | length)}) |
group_by(.decade) | 
map({decade: .[0].decade, count: map(.count) | add}) |
sort_by(.decade) |
.[] | 
"\(.decade): \(.count) albums"
' "$CACHE_FILE"

echo "----------------------------------------"

# Check for potentially invalid years (very old or future)
CURRENT_YEAR=$(date +"%Y")
echo "Checking for unusual release years..."

# Very old releases (before 1950)
jq -r "
.albums_by_year | 
to_entries | 
map(select(.key | tonumber < 1950)) |
.[] | 
\"Year \(.key): \(.value | length) albums\"
" "$CACHE_FILE" > /tmp/old.txt

# Future releases (beyond current year + 1)
jq -r "
.albums_by_year | 
to_entries | 
map(select(.key | tonumber > $((CURRENT_YEAR + 1)))) |
.[] | 
\"Year \(.key): \(.value | length) albums\"
" "$CACHE_FILE" > /tmp/future.txt

OLD_COUNT=$(wc -l < /tmp/old.txt | tr -d ' ')
FUTURE_COUNT=$(wc -l < /tmp/future.txt | tr -d ' ')

if [ "$OLD_COUNT" -eq 0 ] && [ "$FUTURE_COUNT" -eq 0 ]; then
    echo "No unusual years found."
else
    if [ "$OLD_COUNT" -gt 0 ]; then
        echo "Found very old release years (before 1950):"
        cat /tmp/old.txt
    fi
    
    if [ "$FUTURE_COUNT" -gt 0 ]; then
        echo "Found future release years (beyond $(($CURRENT_YEAR + 1))):"
        cat /tmp/future.txt
    fi
fi

# Clean up temp files
rm -f /tmp/duplicates.txt /tmp/old.txt /tmp/future.txt
