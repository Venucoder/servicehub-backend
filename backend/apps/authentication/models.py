from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import secrets

User = get_user_model()


class EmailVerificationToken(models.Model):
    """
    Email verification tokens for new user registrations
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Email verification for {self.user.email}"


class PhoneVerificationToken(models.Model):
    """
    Phone verification tokens (OTP) for phone number verification
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verification_tokens')
    phone_number = models.CharField(max_length=15)
    token = models.CharField(max_length=6)  # 6-digit OTP
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'phone_verification_tokens'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.token:
            import random
            self.token = str(random.randint(100000, 999999))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_max_attempts_reached(self):
        return self.attempts >= self.max_attempts
    
    def __str__(self):
        return f"Phone verification for {self.phone_number}"


class PasswordResetToken(models.Model):
    """
    Password reset tokens for forgot password functionality
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Password reset for {self.user.email}"


class UserSession(models.Model):
    """
    Track user sessions for security and analytics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_info = models.JSONField(default=dict, blank=True)
    location = models.JSONField(default=dict, blank=True)  # City, country, etc.
    
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.username} from {self.ip_address}"


class LoginAttempt(models.Model):
    """
    Track login attempts for security monitoring
    """
    ATTEMPT_TYPES = (
        ('success', 'Successful Login'),
        ('failed_password', 'Failed - Wrong Password'),
        ('failed_user', 'Failed - User Not Found'),
        ('failed_inactive', 'Failed - Inactive Account'),
        ('failed_locked', 'Failed - Account Locked'),
        ('failed_2fa', 'Failed - 2FA Required'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_attempts', null=True, blank=True)
    email = models.EmailField()
    attempt_type = models.CharField(max_length=20, choices=ATTEMPT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Security metadata
    is_suspicious = models.BooleanField(default=False)
    risk_score = models.PositiveIntegerField(default=0)  # 0-100
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['email']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Login attempt: {self.email} - {self.attempt_type}"


class TwoFactorAuth(models.Model):
    """
    Two-factor authentication settings for users
    """
    AUTH_METHODS = (
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('app', 'Authenticator App'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_auth')
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=10, choices=AUTH_METHODS, default='sms')
    
    # For authenticator apps
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    # Recovery
    recovery_codes_used = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'two_factor_auth'
    
    def save(self, *args, **kwargs):
        if not self.secret_key and self.method == 'app':
            import pyotp
            self.secret_key = pyotp.random_base32()
        super().save(*args, **kwargs)
    
    def generate_backup_codes(self):
        """Generate new backup codes"""
        import secrets
        self.backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self.save()
        return self.backup_codes
    
    def __str__(self):
        return f"2FA for {self.user.username} - {self.method}"


class APIKey(models.Model):
    """
    API keys for third-party integrations
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True)
    
    # Permissions
    permissions = models.JSONField(default=list, help_text="List of allowed endpoints/actions")
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    rate_limit = models.PositiveIntegerField(default=1000, help_text="Requests per hour")
    
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_keys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['key']),
            models.Index(fields=['is_active']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"API Key: {self.name} for {self.user.username}"
