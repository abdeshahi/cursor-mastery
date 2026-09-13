from aiogram.fsm.state import State, StatesGroup


class NewRepair(StatesGroup):
    customer_name = State()
    customer_phone = State()
    device = State()
    issue = State()
    technician = State()
    labor_amount = State()
    part_name = State()
    part_cost = State()
    part_sell = State()
    part_supplier = State()
    confirm = State()


class AddTechnician(StatesGroup):
    name = State()
    pct = State()


class AddSupplier(StatesGroup):
    name = State()


class Payment(StatesGroup):
    repair_id = State()
    amount = State()


class SearchRepair(StatesGroup):
    query = State()


class InvoiceLookup(StatesGroup):
    repair_id = State()


class AdminStaffAdd(StatesGroup):
    telegram_id = State()
    name = State()
    role = State()


class AdminTechAdd(StatesGroup):
    name = State()
    pct = State()


class AdminSupAdd(StatesGroup):
    name = State()


class AdminStaffRename(StatesGroup):
    name = State()


class EditRepair(StatesGroup):
    labor_amount = State()
    part_name = State()
    part_cost = State()
    part_sell = State()
    part_supplier = State()


class SettlePayment(StatesGroup):
    choose_payee = State()
