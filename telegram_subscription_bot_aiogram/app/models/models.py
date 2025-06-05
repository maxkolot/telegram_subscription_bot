from tortoise import fields
from tortoise.models import Model

class User(Model):
    """User model for storing user information"""
    
    id = fields.IntField(pk=True)
    user_id = fields.BigIntField(unique=True)
    username = fields.CharField(max_length=255, null=True)
    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)
    language = fields.CharField(max_length=10, default="ru")
    is_admin = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "users"
    
    def __str__(self):
        return f"User {self.user_id}"

class Channel(Model):
    """Channel model for storing channel information"""
    
    id = fields.IntField(pk=True)
    channel_id = fields.BigIntField()
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
    """UserSubscription model for storing user subscriptions"""
    
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="subscriptions")
    channel = fields.ForeignKeyField("models.Channel", related_name="subscribers")
    is_subscribed = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "user_subscriptions"
        unique_together = (("user", "channel"),)
    
    def __str__(self):
        return f"Subscription {self.user} to {self.channel}"

class VideoCircle(Model):
    """VideoCircle model for storing video circle information"""
    
    id = fields.IntField(pk=True)
    short_id = fields.CharField(max_length=36, unique=True)
    file_id = fields.CharField(max_length=255)
    user = fields.ForeignKeyField("models.User", related_name="video_circles")
    status = fields.CharField(max_length=20, default="created")  # created, pending, published, rejected
    channel_post_id = fields.BigIntField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "video_circles"
    
    def __str__(self):
        return f"VideoCircle {self.short_id}"
