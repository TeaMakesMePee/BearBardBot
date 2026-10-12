# Bump VERSION with every release. Set ANNOUNCE = False for versions that are
# just internal/minor bug fixes with nothing user-facing to announce -- the
# version still gets recorded as seen, but no broadcast gets sent.
#
# Keep RELEASE_NOTES high-level and internal-detail-free when ANNOUNCE is True
# -- it gets broadcast to every group chat the bot is in.

VERSION = "1.1.0"
ANNOUNCE = True

RELEASE_NOTES = (
    "What's new:\n"
    "• Member achievements -- unlock badges for activity, milestones, and more\n"
    "• /profile -- view a member's profile card (reply to their message or @mention them)\n"
    "• /achievements -- see every achievement and how to unlock it"
)
