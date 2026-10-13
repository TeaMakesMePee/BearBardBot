# Bump VERSION with every release. Set ANNOUNCE = False for versions that are
# just internal/minor bug fixes with nothing user-facing to announce -- the
# version still gets recorded as seen, but no broadcast gets sent.
#
# Keep RELEASE_NOTES high-level and internal-detail-free when ANNOUNCE is True
# -- it gets broadcast to every group chat the bot is in.

VERSION = "1.3.0"
ANNOUNCE = True

RELEASE_NOTES = (
    "What's new:\n"
    "• Superlatives -- a weekly \"Most Likely To\" poll! Vote on who in the group "
    "fits each superlative; the winner earns bonus EXP. Runs automatically every week."
)
