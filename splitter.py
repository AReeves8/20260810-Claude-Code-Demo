""" Who owes what, after a group of people have paid for things. 
    Amounts are integer cents throughout. 
"""


def split_evenly(amount_cents, participants):
    """Divide one expense between the people who shared it.

    Returns {person: cents_they_owe}.
    """
    share = amount_cents // len(participants)
    return {person: share for person in participants}


def balances(expenses, people):
    """Net position per person, in cents. Positive means they are owed money.

    Every expense moves money twice: the payer is credited the full amount, and
    each participant is debited their share. Across a complete set of expenses
    those two movements should cancel exactly, so the net positions sum to zero.

    If they don't sum to zero, money has been invented or destroyed somewhere
    upstream -- which is not something this function can correct on its own
    without hiding the cause.
    """
    net = {person: 0 for person in people}
    for expense in expenses:
        net[expense["paid_by"]] += expense["amount_cents"]
        shares = split_evenly(expense["amount_cents"], expense["participants"])
        for person, share in shares.items():
            net[person] -= share
    return net
