# Bump VERSION with every release. Set ANNOUNCE = False for versions that are
# just internal/minor bug fixes with nothing user-facing to announce -- the
# version still gets recorded as seen, but no broadcast gets sent.
#
# Keep RELEASE_NOTES high-level and internal-detail-free when ANNOUNCE is True
# -- it gets broadcast to every group chat the bot is in.

VERSION = "1.3.1"
ANNOUNCE = True

RELEASE_NOTES = (
    "What's new:\n"
    "• Fixed a bug where the 🦉 Night Owl achievement was checking the wrong "
    "timezone, so it almost never unlocked for actual late-night messages. "
    "It now correctly tracks 2am-5am local time."
)
