import random
import uuid
from datetime import datetime, timedelta, timezone

from .database import SessionLocal
from .models import User, Event, Friendship, EventVisibility
from .wizard.wizard_utils import TOPICS, EVENT_OPTIONS

# City → bounding box (lat_min, lat_max, lon_min, lon_max)
# Moscow is listed multiple times to make it more likely in random choices.
CITY_CHOICES = [
    ("Moscow", 55.55, 55.95, 37.35, 37.85),
    ("Moscow", 55.55, 55.95, 37.35, 37.85),
    ("Moscow", 55.55, 55.95, 37.35, 37.85),
    ("Moscow", 55.55, 55.95, 37.35, 37.85),
    ("Moscow", 55.55, 55.95, 37.35, 37.85),
    ("Saint Petersburg", 59.8, 60.1, 30.1, 30.6),
    ("Novosibirsk", 54.9, 55.2, 82.8, 83.2),
    ("Yekaterinburg", 56.75, 56.95, 60.5, 60.7),
    ("Kazan", 55.7, 55.9, 49.0, 49.3),
    ("Nizhny Novgorod", 56.2, 56.4, 43.8, 44.1),
    ("Samara", 53.1, 53.3, 50.0, 50.3),
    ("Omsk", 54.9, 55.1, 73.2, 73.4),
    ("Chelyabinsk", 55.1, 55.2, 61.35, 61.55),
    ("Rostov-on-Don", 47.15, 47.3, 39.55, 39.85),
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
                city, lat_min, lat_max, lon_min, lon_max = random.choice(CITY_CHOICES)
                lat = random.uniform(lat_min, lat_max)
                lon = random.uniform(lon_min, lon_max)
                vis = random.choice(list(EventVisibility))
                ev = Event(
                    id=str(uuid.uuid4()),
                    owner_id=fid,
                    title=title,
                    description="test event",
                    datetime_utc=dt,
                    location_txt=city,
                    latitude=lat,
                    longitude=lon,
                    address=city,
                    visibility=vis,
                    tags=topic,
                )
                db.add(ev)

        db.commit()
