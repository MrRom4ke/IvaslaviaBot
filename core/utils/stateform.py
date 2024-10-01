from aiogram.fsm.state import StatesGroup, State

class ApplicationForm(StatesGroup):
    WAITING_FOR_SCREEN = State()
    PAYMENT_CONFIRMATION = State()