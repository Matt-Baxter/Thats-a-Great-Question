"""The written list of angles a question may take.

This is the answer to "how does the app decide what to ask?" Each entry names one
angle from which a seed can be questioned, with one sentence the model reads telling
it what that angle looks for. The whole list goes into every prompt; the model draws
on it to write candidates and to make sure a set covers different angles (FR-008).

The list guides generation only. It is never shown to the user, and no returned
question carries a label saying which angle it came from (FR-012).
"""

LINES_OF_INQUIRY = [
    # What has to be true for the seed to hold, but has not been said.
    {
        "name": "assumption",
        "description": "Surfaces something the seed takes for granted without stating it.",
    },
    # What would show the seed to be right or wrong, and how anyone would know.
    {
        "name": "evidence",
        "description": "Asks what observation, data or experience would confirm or undermine the seed.",
    },
    # What follows if the seed is true, including effects nobody intended.
    {
        "name": "consequence",
        "description": "Follows the seed forward to what it would lead to, including second-order effects.",
    },
    # Other explanations or courses of action the seed passes over.
    {
        "name": "alternative",
        "description": "Asks what else could explain the situation or what other path could be taken.",
    },
    # Who is affected, who decides, and whose view is missing.
    {
        "name": "stakeholder",
        "description": "Asks who is affected by the seed, who has a say in it, and whose view is absent.",
    },
    # A key word or idea that could mean different things to different people.
    {
        "name": "definition",
        "description": "Picks out a term in the seed whose meaning is unclear or contested and asks what it means here.",
    },
    # How the seed is posed, and what that way of posing it hides or rules out.
    {
        "name": "framing",
        "description": "Questions the way the seed is put, and what a different framing would bring into view.",
    },
    # What has happened before in similar situations, and what that suggests.
    {
        "name": "precedent",
        "description": "Asks what history or comparable cases suggest about the seed.",
    },
    # What rewards or pressures push the people involved one way or another.
    {
        "name": "incentive",
        "description": "Asks what motivates the people involved and how that shapes what happens.",
    },
    # How the idea, plan or claim could go wrong, and what would be the first sign.
    {
        "name": "failure mode",
        "description": "Asks how the seed could fail or turn out wrong, and what the earliest warning would be.",
    },
]
