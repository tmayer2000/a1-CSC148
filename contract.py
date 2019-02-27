"""
CSC148, Winter 2019
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2019 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This is an abstract class. Only subclasses should be instantiated.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.datetime
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """
    a type of Contract with a specific start date and end date, and which
    requires a commitment until the end date.

    A subclass of Contract class
    ==Public Attributes==
    start:
        starting date for the term of the contract
    end:
        ending date for the term of the contract
    bill:
        bill for this contract for the last month of call records loaded from
        the input dataset
    cur_month:
        current month of the contract
    cur_year:
        current year of the contract
    """
    start: datetime.datetime
    end: datetime.datetime
    bill: Optional[Bill]
    cur_month: datetime.datetime.month
    cur_year: datetime.datetime.year


    def __init__(self, start: datetime.datetime, end: datetime.datetime)->None:
        self.start = start
        self.end = end
        self.bill = Bill()
        self.cur_month = start.month
        self.cur_year = start.year

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        if month == self.start.month and year == self.start.year:
            bill.set_rates('TERM', TERM_MINS_COST)
            bill.add_fixed_cost(TERM_DEPOSIT + TERM_MONTHLY_FEE)
            bill.add_free_minutes(TERM_MINS)
        else:
            bill.set_rates('TERM', TERM_MINS_COST)
            bill.add_fixed_cost(TERM_MONTHLY_FEE)
            bill.add_free_minutes(TERM_MINS)
        self.bill = bill
        self.cur_month = month
        self.cur_year = year

    def bill_call(self, call: Call) -> None:
        dur = (ceil(call.duration / 60))
        if self.bill.free_min == 0:
            self.bill.add_billed_minutes(dur)
        elif (self.bill.free_min - dur) > 0:
            self.bill.free_min -= dur
        elif (self.bill.free_min - dur) < 0:
            while self.bill.free_min > 0:
                dur -= 1
                self.bill.free_min -= 1
            self.bill.add_billed_minutes(dur)

    def cancel_contract(self) -> float:
        self.start = None
        if self.cur_year >= self.end.year:
            if self.cur_month > self.end.month:
                return self.bill.get_cost() - 300
            else:
                return self.bill.get_cost()
        else:
            return self.bill.get_cost()


class MTMContract(Contract):
    """
    Contract with no end date and no initial term deposit

    A subclass of Contract
    ==Public Attributes==
    start:
        start date of the contract
    bill:
        bill for this contract for the last month of call records loaded from
        the input dataset
    """
    start: datetime.datetime
    bill: Optional[Bill]

    def __init__(self, start: datetime.datetime) -> None:
        self.start = start
        self.bill = Bill()

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        bill.set_rates('MTM', MTM_MINS_COST)
        bill.add_fixed_cost(MTM_MONTHLY_FEE)
        self.bill = bill

    def bill_call(self, call: Call) -> None:
        dur = (ceil(call.duration / 60))
        self.bill.add_billed_minutes(dur)

    def cancel_contract(self) -> float:
        self.start = None
        return self.bill.get_cost()


class PrepaidContract(Contract):
    """
    A prepaid contract has a start date but does not have an end date,
    and it comes with no included minutes. It has an associated balance,
    which is the amount of money the customer owes.

    A subclass of Contract
    ==Public Attributes==
    start:
        the start date of the contract
    bill:
         bill for this contract for the last month of call records loaded from
        the input dataset
    balance:
        the current balance associated with this contract
    """
    start: datetime.datetime
    bill: Optional[Bill]
    balance: float

    def __init__(self, start: datetime.datetime, balance: float) -> None:
        self.start = start
        self.balance = -balance
        self.bill = Bill()


    def add_to_balance(self, amount: float) -> None:
        """
        used to add balance to a prepaid contract
        """
        self.balance -= amount
        self.bill.add_fixed_cost(-amount)


    def new_month(self, month: int, year: int, bill: Bill) -> None:
        bill.set_rates('PREPAID', PREPAID_MINS_COST)
        if self.balance > -10:
            amount_to_add = -25 - self.balance
            self.add_to_balance(amount_to_add)
        else:
            bill.add_fixed_cost(self.balance)
        self.bill = bill


    def bill_call(self, call: Call) -> None:
        dur = (ceil(call.duration / 60))
        self.bill.add_billed_minutes(dur)
        self.balance += (self.bill.min_rate * dur)

    def cancel_contract(self) -> float:
        self.start = None
        if self.balance > 0:
            return self.balance
        else:
            return None





















if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
