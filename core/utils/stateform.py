from aiogram.fsm.state import StatesGroup, State


class StepsForm(StatesGroup):
    GET_NAME = State()
    GET_SURNAME = State()
    GET_AGE = State()

    GET_SCREEN = State()
    CHECK_IMAGE = State()