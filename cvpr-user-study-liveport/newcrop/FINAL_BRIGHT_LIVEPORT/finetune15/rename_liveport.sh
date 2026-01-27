#!/bin/bash

OLD="heygen"
NEW="liveport"

# Bottom-up traversal to avoid path breakage
find . -depth -name "*${OLD}*" | while read -r path; do
    newpath="$(dirname "$path")/$(basename "$path" | sed "s/${OLD}/${NEW}/g")"
    if [ "$path" != "$newpath" ]; then
        mv "$path" "$newpath"
    fi
done
