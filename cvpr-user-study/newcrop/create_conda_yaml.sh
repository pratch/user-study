# 1. Export the history of conda-installed packages
#    (This is the portable, minimal set of conda dependencies)
conda env export --from-history > environment.yaml

# 2. Add the 'pip' dependency section to the file
#    (If 'pip' isn't already listed in the 'dependencies:' section, this ensures it is.)
echo '  - pip' >> environment.yaml

# 3. Use a temporary file to get the list of pip packages
#    (We filter out the first two lines, 'name:' and 'channels:', from the full export)
conda env export | grep -A 9999 '  - pip:' | grep -v 'name:' | grep -v 'channels:' >> environment.yaml

# 4. Remove the 'prefix' line (optional, but improves portability)
grep -v '^prefix:' environment.yaml > environment_clean.yaml
mv environment_clean.yaml environment.yaml