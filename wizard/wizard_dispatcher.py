# wizard/wizard_dispatcher.py

from telebot import types
from .wizard import get as wiz_get, reset as wiz_reset
from .steps.step0_topic import handle as handle_step0
from .steps.step1_event import handle as handle_step1
from .steps.step2_datetime import handle as handle_step2
from .steps.step3_location import handle as handle_step3
from .steps.step4_visibility import handle as handle_step4
from .steps.step5_picture import handle as handle_step5
from .steps.step6_description import handle as handle_step6

# Map numeric step → handler(bot, message, wizard_state)
step_handlers = {
    0: handle_step0,
    1: handle_step1,
    2: handle_step2,
    3: handle_step3,
    4: handle_step4,
    5: handle_step5,
    6: handle_step6,
}

def register_dispatcher(bot):
    """
    Registers one message_handler that fires whenever wiz_get(uid) != None. 
    Then it does a “cancel” check, and finally dispatches to the proper step.
    """
    # @bot.message_handler(func=lambda m: wiz_get(m.from_user.id) is not None)
    @bot.message_handler(
        func=lambda m: wiz_get(m.from_user.id) is not None,
        content_types=['text', 'location', 'venue', 'photo']
    )
    def _wizard_steps(m):
        user_id = m.from_user.id
        w = wiz_get(user_id)
        if not w:
            return

        # 1) Cancel at any time
        if m.text == "cancel":
            wiz_reset(user_id)
            from ..bot import MAIN_KB
            bot.send_message(user_id, "Operation cancelled. Back to main menu.", reply_markup=MAIN_KB)
            return

        # 2) Dispatch to correct handler based on w["step"]
        step = w["step"]
        handler = step_handlers.get(step)
        if handler:
            handler(bot, m, w)
        else:
            # If for some reason step is out of range, reset and inform user
            wiz_reset(user_id)
            from ..bot import MAIN_KB
            bot.send_message(
                user_id,
                "An error occurred in the wizard. Returning to main menu.",
                reply_markup=MAIN_KB
            )
