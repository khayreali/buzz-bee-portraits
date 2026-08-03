#!/bin/sh
# Download the reference portraits the generator sends with every request, then
# crop them to the bust composition this project uses.
#
# The originals come from block/buzz, which is Apache-2.0. They are saved
# unmodified under refs/originals. See refs/LICENSE.
#
# Needs Pillow for the crop step: pip install -r requirements.txt

set -e

here=$(cd "$(dirname "$0")" && pwd)
base="https://raw.githubusercontent.com/block/buzz/main/desktop/public/onboarding/starter-team"

mkdir -p "$here/originals"

for name in fizz honey bumble; do
    echo "downloading $name.png"
    curl -fsSL "$base/$name.png" -o "$here/originals/$name.png"
done

echo
python3 "$here/make_references.py"

echo
echo "reference portraits are in $here"
ls -l "$here"/*.png
