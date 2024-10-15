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

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    credit:
        balance of the customer
    """
    start: datetime.date
    bill: Optional[Bill]
    credit: int

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>.
        This may be the first month of the contract.
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


class MTMContract(Contract):
    """
    A type of contract called Month-To-Month with no initial deposit
    or term commitment.

    This contract does not come with free minutes.
    """

    def __init__(self, start: datetime.date) -> None:
        Contract.__init__(self, start)

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>.
        This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost. Also adds the monthly fee and cost per minute
        to call.

        Precondition
        - Last month's bill has been paid successfully
        """
        self.bill = bill
        self.bill.add_fixed_cost(MTM_MONTHLY_FEE)
        self.bill.set_rates("MTM", MTM_MINS_COST)


class TermContract(Contract):
    """
    A type of contract called Term Contract. There is a set start and end date,
    but can continue past the end date until you cancel.

    This contract has a lower monthly cost than MTM, lower calling rates,
    and free calling minutes.


    === Public Attributes ===
    end_date:
        The set date for the Term Contract to end
    free:
        The number of free minutes given in the term contract

    === Private Attributes ===
    _curr_month:
        stores the current month of the bill instated when
        new_month is run.
        Also used to check if we refund the deposit once
        cancel_contract is run.
    _curr_year:
        stores the current year of the bill instated when
        new_month is run.
        Also used to check if we refund the deposit once
        cancel_contract is run.
    """
    end_date: datetime.date
    _free: float
    _curr_month: int
    _curr_year: int

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """
        Initializes the start date and end date of the term contract.
        Also stores the amount of free mins given.
        """
        Contract.__init__(self, start)
        self.end_date = end
        self._free = TERM_MINS

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>.
        This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost. Also adds the monthly fee and cost per minute
        to call.

        Precondition
        - Last month's bill has been paid successfully
        """
        self.bill = bill

        # Checks if the term deposit needs to be added to the fixed cost
        if month == self.start.month and year == self.start.year:
            self.bill.add_fixed_cost(TERM_DEPOSIT)

        self.bill.add_fixed_cost(TERM_MONTHLY_FEE)
        self.bill.set_rates("TERM", TERM_MINS_COST)
        self._free = TERM_MINS
        self._curr_month = month
        self._curr_year = year

    def bill_call(self, call: Call) -> None:
        """
        Adds the amount of free minutes and billed minutes
        based on the amount of free minutes left

        Precondition:
        - A bill has already been created for the corresponding month
        """
        mins = ceil(call.duration / 60.0)

        # checks if the duration of the call exceeds the amount
        # of free minutes available and bills accordingly
        if mins <= self._free:
            self.bill.add_free_minutes(mins)
            self._free -= mins
        else:
            self.bill.add_free_minutes(ceil(self._free / 60.0))
            mins -= self._free
            self._free = 0
            self.bill.add_billed_minutes(mins)

    def cancel_contract(self) -> float:
        """
        Cancels the contract and returns the term deposit
        based on the time the contract is cancelled.
        """
        # To determine if the term deposit should be refunded
        if (self._curr_year >= self.end_date.year
                and self._curr_month > self.end_date.month):
            return self.bill.get_cost() - TERM_DEPOSIT
        return self.bill.get_cost()


class PrepaidContract(Contract):
    """
    A Prepaid Contract is a type of contract in which a customer
    has a credit balance.


    === Public Attributes ===
    balance:
        The credit balance for the contract. If the balance is negative,
        it represents the amount of credit the customer has.
        If the balance is positive, it represents the amount
        of credit the customer owes.
    """
    balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        """
        Initializes the contract with a corresponding start
        date and credit based on the balance. If the balance is
        negative, that represents credit.
        """
        Contract.__init__(self, start)
        # Negative balance indicates credit
        self.balance = balance * -1

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>.
        This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost. Also adds the monthly fee and cost per minute
        to call.

        Precondition
        - Last month's bill has been paid successfully
        """
        self.bill = bill
        self.bill.set_rates("PREPAID", PREPAID_MINS_COST)
        if self.balance > -10:
            self.balance -= 25

        # Carrying over the credit from the previous bill to this one
        self.bill.add_fixed_cost(self.balance)

    def bill_call(self, call: Call) -> None:
        """
        Adds billed minutes to the monthly bill based on the
        duration of the call then updates the balance.

        Precondition:
        - A bill has already been created for the corresponding month
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))
        self.balance = self.bill.get_cost()

    def cancel_contract(self) -> float:
        """
        Cancels the contract and returns the amount due.
        If there is credit, it is forfeited.
        """
        if self.balance > 0:
            return self.balance
        return 0
