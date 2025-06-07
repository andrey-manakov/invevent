import random
import uuid
from datetime import datetime, timedelta, timezone

from .database import SessionLocal
from .models import User, Event, Friendship, EventVisibility
from .wizard.wizard_utils import TOPICS, EVENT_OPTIONS

# Cities list with bias towards Moscow
CITIES = [
    "Moscow", "Moscow", "Moscow", "Moscow", "Moscow",  # heavier weight
    "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan",
    "Nizhny Novgorod", "Samara", "Omsk", "Chelyabinsk", "Rostov-on-Don"
]


def generate_test_data(user_id: int) -> None:
    """Populate database with fake friends and events for `user_id`."""
    with SessionLocal() as db:
        # ensure user exists
        if not db.get(User, user_id):
            db.add(User(id=user_id, first_name=f"User{user_id}", username=None))
            db.commit()

        for i in range(10):
            # unique friend id
            while True:
                fid = random.randint(10_000_000, 99_999_999)
                if fid != user_id and db.get(User, fid) is None:
                    break
            db.add(User(id=fid, first_name=f"Friend{i+1}", username=f"friend{i+1}"))

            relation = random.choice(["mutual", "user_to_friend", "friend_to_user"])
            if relation in ("mutual", "user_to_friend"):
                db.add(Friendship(follower_id=user_id, followee_id=fid))
            if relation in ("mutual", "friend_to_user"):
                db.add(Friendship(follower_id=fid, followee_id=user_id))

            for _ in range(random.randint(3, 10)):
                topic = random.choice(TOPICS)
                title_opts = EVENT_OPTIONS.get(topic, ["other"])
                title = random.choice(title_opts)
                dt = datetime.now(timezone.utc) + timedelta(days=random.randint(0, 30))
                city = random.choice(CITIES)
                vis = random.choice(list(EventVisibility))
                ev = Event(
                    id=str(uuid.uuid4()),
                    owner_id=fid,
                    title=title,
                    description="test event",
                    datetime_utc=dt,
                    location_txt=city,
                    visibility=vis,
                    tags=topic,
                )
                db.add(ev)

        db.commit()
