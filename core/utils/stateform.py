from aiogram.fsm.state import StatesGroup, State

class ApplicationForm(StatesGroup):
    WAITING_FOR_SCREEN = State()
    WAITING_FOR_PAYMENT_SCREEN = State()

class NewDrawingState(StatesGroup):
    title = State()
    description = State()
    start_date = State()
    end_date = State()
    max_participants = State()