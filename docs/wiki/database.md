# Database model

The bot uses SQLAlchemy with a small set of tables:

| Table | Description |
|-------|-------------|
| **User** | Telegram user ID, first name and optional username. |
| **Event** | Individual event created through the wizard. Stores title,
  description, datetime in UTC, optional coordinates or free-text address and
  visibility. |
| **Participation** | Link table recording which users joined which events. |
| **Friendship** | Simple follow relation: `follower_id` -> `followee_id`. Used
  to show friends' events. |

SQLite is used by default but any SQLAlchemy compatible URL can be supplied via
`DB_URL`.
