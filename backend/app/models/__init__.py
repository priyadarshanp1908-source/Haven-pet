# Haven Pet — Models package
# Import all models here so Alembic/Base.metadata can discover them.

from app.models.user import User  # noqa: F401
from app.models.pet import Pet  # noqa: F401
from app.models.vaccination import Vaccination  # noqa: F401
from app.models.medication import Medication  # noqa: F401
from app.models.behavior_log import BehaviorLog  # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.chat_message import ChatMessage  # noqa: F401
from app.models.notification import Notification  # noqa: F401
