#!/bin/bash

OLD="finetune15_rebuttal_liveportrait"
NEW="finetune15"

# Traverse bottom-up to avoid breaking paths mid-walk
find . -depth -name "${OLD}*" | while read -r path; do
    newpath="$(dirname "$path")/$(basename "$path" | sed "s/^$OLD/$NEW/")"
    if [ "$path" != "$newpath" ]; then
        mv "$path" "$newpath"
    fi
done
