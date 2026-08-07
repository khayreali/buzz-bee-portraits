#!/bin/sh
# Install the bee portrait skill into your Buzz application.
#
# From a checkout:
#   ./install.sh
#
# Without cloning anything:
#   curl -fsSL https://raw.githubusercontent.com/khayreali/buzz-bee-portraits/main/install.sh | sh
#
# Check an existing install instead of writing anything:
#   ./install.sh --check
#   curl -fsSL https://raw.githubusercontent.com/khayreali/buzz-bee-portraits/main/install.sh | sh -s -- --check
#
# Set BUZZ_NEST if your agents do not run in ~/.buzz.

set -e

REPOSITORY="khayreali/buzz-bee-portraits"
BRANCH="main"
NEST="${BUZZ_NEST:-$HOME/.buzz}"
TARGET="$NEST/.agents/skills/bee-portrait"

# The real copy lives under .agents/skills so every runtime shares one install,
# and each runtime only reads its own directory. Buzz Desktop does exactly this
# for its own buzz-cli skill, so a symlink per runtime is the shape to match.
# Without the link the skill sits on disk and no agent can ever see it.
RUNTIME_DIRECTORIES=".claude/skills .goose/skills .codex/skills"

# Everything install_from copies. Checked before anything is deleted, so a bad
# or half downloaded source cannot leave a working install in pieces.
REQUIRED="skills/bee-portrait/SKILL.md bin/generate_bee.py bin/assemble_bee.py bin/clay_colours.py bin/components.json LICENSE NOTICE refs/LICENSE"

say() {
    printf '%s\n' "$1"
}

check_python() {
    if command -v python3 >/dev/null 2>&1; then
        say "  python3      $(python3 --version 2>&1)"
    else
        say "  python3      MISSING. Install Python 3.9 or newer."
        return 1
    fi
}

check_key() {
    if [ -n "$GEMINI_API_KEY" ]; then
        say "  api key      set"
    else
        say "  api key      not set in this shell"
        say "               Buzz Desktop: Settings, Agents, Agent defaults,"
        say "               Advanced, Environment variables. Add GEMINI_API_KEY."
        say "               Or in a shell: export GEMINI_API_KEY=your-key"
        say "               Get a key at https://aistudio.google.com/apikey"
    fi
}

run_check() {
    say "bee portrait check"
    say ""

    have_python=yes
    check_python || have_python=no

    if [ -f "$TARGET/SKILL.md" ]; then
        say "  skill        $TARGET"
    else
        say "  skill        not installed"
    fi

    if [ -f "$TARGET/bin/components.json" ]; then
        count=$(ls "$TARGET/refs"/*.png 2>/dev/null | wc -l | tr -d ' ')
        say "  scripts      installed, $count reference portraits"
    else
        say "  scripts      not installed"
    fi

    # An install nothing links to is invisible to every agent, so report the
    # links rather than letting a green looking check hide it.
    found=""
    for relative in $RUNTIME_DIRECTORIES; do
        if [ -L "$NEST/$relative/bee-portrait" ]; then
            found="$found $relative"
        fi
    done
    if [ -n "$found" ]; then
        say "  loaded by   $found"
    else
        say "  loaded by   NOTHING. No runtime is linked to this install,"
        say "              so no agent can see the skill. Reinstall to fix it."
    fi

    check_key
    say ""

    if [ "$have_python" = yes ] && [ -f "$TARGET/bin/generate_bee.py" ]; then
        say "Try it, this one is free and makes no network call:"
        say "  python3 $TARGET/bin/generate_bee.py --seed 7 --dry-run --out /dev/null"
        return 0
    fi

    if [ ! -f "$TARGET/bin/generate_bee.py" ]; then
        say "Nothing is installed here. To install it:"
        say "  curl -fsSL https://raw.githubusercontent.com/$REPOSITORY/$BRANCH/install.sh | sh"
    fi
    return 1
}

check_source() {
    source_directory="$1"
    for required in $REQUIRED; do
        if [ ! -e "$source_directory/$required" ]; then
            return 1
        fi
    done
    return 0
}

install_from() {
    source_directory="$1"

    if ! check_source "$source_directory"; then
        say "that does not look like a complete bee portrait repository:"
        say "  $source_directory"
        exit 1
    fi

    # Build the new install beside the old one, then swap. If anything fails
    # part way through, the install you already had is untouched.
    staging="$TARGET.new"
    mkdir -p "$NEST/.agents/skills"
    rm -rf "$staging"

    cp -R "$source_directory/skills/bee-portrait" "$staging"

    # The skill ships with the scripts and references inside it, so an agent
    # never has to find a separate checkout.
    cp -R "$source_directory/bin" "$staging/bin"
    mkdir -p "$staging/refs"
    for portrait in "$source_directory/refs"/*.png; do
        if [ -f "$portrait" ]; then
            cp "$portrait" "$staging/refs/"
        fi
    done
    cp "$source_directory/refs/LICENSE" "$staging/refs/LICENSE"
    cp "$source_directory/LICENSE" "$staging/LICENSE"
    cp "$source_directory/NOTICE" "$staging/NOTICE"

    rm -rf "$staging/bin/__pycache__"

    # roster.json is measured from whoever's portraits, so it belongs to the
    # person who ran the tool. Never carry the maintainer's copy to a stranger.
    rm -f "$staging/bin/roster.json"

    chmod +x "$staging/bin/assemble_bee.py" "$staging/bin/generate_bee.py" \
        "$staging/bin/clay_colours.py"

    # components.json is the file the documentation tells people to edit, and
    # roster.json is the file they are told to generate. Keep the old install
    # rather than deleting work without asking.
    if [ -d "$TARGET" ]; then
        rm -rf "$TARGET.previous"
        mv "$TARGET" "$TARGET.previous"
        kept="yes"
    fi

    mv "$staging" "$TARGET"

    link_runtimes
}

# Point every runtime that is set up in this nest at the copy we just installed.
link_runtimes() {
    linked=""
    for relative in $RUNTIME_DIRECTORIES; do
        runtime_directory="$NEST/$relative"
        runtime_root=$(dirname "$runtime_directory")

        # Only wire up a runtime the person actually uses. Creating .goose for
        # somebody who runs Claude Code would just be litter in their nest.
        if [ ! -d "$runtime_root" ]; then
            continue
        fi

        mkdir -p "$runtime_directory"
        link="$runtime_directory/bee-portrait"
        rm -rf "$link"
        ln -s "../../.agents/skills/bee-portrait" "$link"
        linked="$linked $relative"
    done

    # No runtime directory at all means a nest that has not been set up yet.
    # Claude Code is the common case, so leave the skill somewhere it will be
    # found rather than installing it where nothing reads.
    if [ -z "$linked" ]; then
        mkdir -p "$NEST/.claude/skills"
        link="$NEST/.claude/skills/bee-portrait"
        rm -rf "$link"
        ln -s "../../.agents/skills/bee-portrait" "$link"
        linked=" .claude/skills"
    fi
}

download_and_install() {
    if ! command -v curl >/dev/null 2>&1; then
        say "curl is not installed."
        say "Install curl, or clone the repository and run ./install.sh from it."
        exit 1
    fi

    say "downloading $REPOSITORY"
    temporary=$(mktemp -d)
    trap 'rm -rf "$temporary"' EXIT INT HUP TERM

    if ! curl -fsSL \
        "https://codeload.github.com/$REPOSITORY/tar.gz/refs/heads/$BRANCH" \
        -o "$temporary/source.tar.gz"; then
        say "could not download $REPOSITORY."
        say "Check your network connection and try again."
        exit 1
    fi

    if ! tar xzf "$temporary/source.tar.gz" -C "$temporary"; then
        say "the download was damaged. Try again."
        exit 1
    fi

    extracted=""
    for candidate in "$temporary"/*-"$BRANCH"; do
        if [ -d "$candidate" ]; then
            extracted="$candidate"
        fi
    done

    if [ -z "$extracted" ]; then
        say "the download did not contain the expected files."
        exit 1
    fi

    install_from "$extracted"
}

case "$1" in
    --check)
        status=0
        run_check || status=$?
        exit $status
        ;;
    --help | -h)
        say "usage: install.sh [--check]"
        say ""
        say "  no option  install the skill into \$BUZZ_NEST, default ~/.buzz"
        say "  --check    report the state of an existing install, write nothing"
        exit 0
        ;;
    "") ;;
    *)
        say "unknown option: $1"
        say "usage: install.sh [--check]"
        exit 1
        ;;
esac

if [ ! -d "$NEST" ]; then
    say "No Buzz directory at $NEST."
    say "If your agents run somewhere else, set BUZZ_NEST and try again:"
    say "  BUZZ_NEST=/path/to/nest ./install.sh"
    exit 1
fi

# Only treat $0 as a path when it looks like one. Piped into sh, $0 is "sh",
# and dirname turns that into the current directory, which would silently
# install whatever checkout the user happens to be standing in.
here=""
case "$0" in
    */*) here=$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo "") ;;
esac

if [ -n "$here" ] && check_source "$here"; then
    say "installing from $here"
    install_from "$here"
else
    download_and_install
fi

say "Installed to $TARGET"

if [ "$kept" = "yes" ]; then
    say ""
    say "Your previous install was kept at:"
    say "  $TARGET.previous"
    say "If you had edited components.json or generated roster.json, copy them"
    say "across from there. Reinstalling again replaces that copy."
fi

say ""
run_check || true
say ""
say "Restart your agent and the bee-portrait skill will be available."
