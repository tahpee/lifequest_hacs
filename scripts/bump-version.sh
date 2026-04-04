#!/bin/bash
# Bumps the patch version in manifest.json
set -e

MANIFEST="custom_components/lifequest/manifest.json"
VERSION=$(grep -o '"version": "[^"]*"' "$MANIFEST" | cut -d'"' -f4)
IFS='.' read -r major minor patch <<< "$VERSION"
NEW_VERSION="$major.$minor.$((patch + 1))"

sed -i '' "s/\"version\": \"$VERSION\"/\"version\": \"$NEW_VERSION\"/" "$MANIFEST"
echo "Bumped $VERSION -> $NEW_VERSION"
