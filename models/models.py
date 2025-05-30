from tortoise import fields
from tortoise.models import Model

class User(Model):
    """User model for storing telegram user information"""
    id = fields.IntField(pk=True)
    telegram_id = fields.BigIntField(unique=True)
    language = fields.CharField(max_length=2, default="ru")
    is_active = fields.BooleanField(default=True)
    subscription_status = fields.BooleanField(default=False)
    subscription_type = fields.CharField(max_length=20, default="free")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"User {self.telegram_id}"


class Channel(Model):
    """Channel model for storing subscription channels"""
    id = fields.IntField(pk=True)
    channel_id = fields.CharField(max_length=255)
    channel_name = fields.CharField(max_length=255)
    channel_link = fields.CharField(max_length=255)
    button_text = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "channels"

    def __str__(self):
        return f"Channel {self.channel_name}"


class UserSubscription(Model):
    """Model for tracking user subscriptions to channels"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='subscriptions')
    channel = fields.ForeignKeyField('models.Channel', related_name='subscribers')
    is_subscribed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_subscriptions"
        unique_together = (("user", "channel"),)

    def __str__(self):
        return f"Subscription {self.user_id} to {self.channel_id}"


class VideoCircle(Model):
    """Model for storing video circles and their file_ids"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='video_circles')
    file_id = fields.CharField(max_length=255)
    short_id = fields.CharField(max_length=10, unique=True)
    status = fields.CharField(max_length=20, default="created")  # created, pending, published, rejected
    published_message_id = fields.BigIntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "video_circles"

    def __str__(self):
        return f"VideoCircle {self.id} by User {self.user_id}"
