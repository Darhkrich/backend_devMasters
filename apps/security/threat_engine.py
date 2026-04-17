from datetime import timedelta

from django.utils import timezone

from apps.security.models import BlockedIP, IPActivity, SuspiciousIP, TrustedIP


class ThreatEngine:
    BLOCK_DURATION = timedelta(minutes=30)
    RATE_LIMIT = 100
    RATE_WINDOW = timedelta(minutes=1)
    RISK_BLOCK_THRESHOLD = 100
    REQUEST_RISK_THRESHOLD = 80

    @staticmethod
    def is_blocked(ip):
        if not ip:
            return False

        blocked = BlockedIP.objects.filter(ip_address=ip).first()
        if not blocked:
            return False

        if blocked.is_expired():
            blocked.delete()
            return False

        return True

    @staticmethod
    def block_ip(obj, reason="Too many failed login attempts"):
        obj.block_count += 1
        obj.save(update_fields=["block_count"])

        duration = ThreatEngine.BLOCK_DURATION * max(obj.block_count, 1)
        max_duration = timedelta(hours=24)
        duration = min(duration, max_duration)
        BlockedIP.objects.update_or_create(
            ip_address=obj.ip_address,
            defaults={
                "reason": reason,
                "blocked_until": timezone.now() + duration,
                "attempts": obj.failed_logins,
                "block_count": obj.block_count,
            },
        )



    @staticmethod
    def record_successful_login(ip, user=None):
        if not ip:
            return

        obj, _ = SuspiciousIP.objects.get_or_create(ip_address=ip)
        ThreatEngine.decay_risk(obj)

        obj.failed_logins = 0
        obj.request_count = 0
        obj.risk_score *= 0.3
        obj.last_success = timezone.now()

        obj.save(update_fields=[
            "failed_logins",
            "request_count",
            "risk_score",
            "last_success",
            "last_attempt",
        ])

        # 🔥 TRUST THIS IP
        if user:
            TrustedIP.objects.get_or_create(ip_address=ip, user=user)

        # 🔥 REMOVE BLOCK
        BlockedIP.objects.filter(ip_address=ip).delete()

    @staticmethod
    def check_rate_limit(ip):
        if not ip:
            return True

        obj, _ = SuspiciousIP.objects.get_or_create(ip_address=ip)
        now = timezone.now()

        if obj.last_attempt and now - obj.last_attempt > ThreatEngine.RATE_WINDOW:
            obj.request_count = 0

        obj.request_count += 1
        obj.last_attempt = now

        if obj.request_count > ThreatEngine.RATE_LIMIT:
            obj.risk_score += 10
            if obj.risk_score >= ThreatEngine.RISK_BLOCK_THRESHOLD:
                ThreatEngine.block_ip(obj, reason="Too many requests")

        obj.save(update_fields=["request_count", "risk_score", "last_attempt"])
        return obj.request_count <= ThreatEngine.RATE_LIMIT

    @staticmethod
    def decay_risk(obj):
        if not obj.last_attempt:
            return

        minutes_passed = (timezone.now() - obj.last_attempt).total_seconds() / 60

        decay_factor = 0.9 ** minutes_passed
        obj.risk_score = max(obj.risk_score * decay_factor, 0)

        # 🔥 FULL RESET WHEN SAFE
        if obj.risk_score < 5:
            obj.failed_logins = 0
            obj.request_count = 0

    @staticmethod
    def record_failed_login(ip):
        if not ip:
            return

        obj, _ = SuspiciousIP.objects.get_or_create(ip_address=ip)
        ThreatEngine.decay_risk(obj)

        obj.failed_logins += 1
        increment = 10 + (obj.failed_logins ** 1.5)
        obj.risk_score += min(increment, 60)
        obj.last_attempt = timezone.now()
        obj.save(update_fields=["failed_logins", "risk_score", "last_attempt"])

        if obj.risk_score >= ThreatEngine.RISK_BLOCK_THRESHOLD:
            ThreatEngine.block_ip(obj)

    @staticmethod
    def update_request(ip):
        activity, _ = IPActivity.objects.get_or_create(ip_address=ip)
        now = timezone.now()

        if activity.last_request and now - activity.last_request > ThreatEngine.RATE_WINDOW:
            activity.request_count = 0

        activity.request_count += 1
        activity.last_request = now
        activity.risk_score = ThreatEngine.calculate_risk(activity)
        activity.save(update_fields=["request_count", "last_request", "risk_score"])
        return activity

    @staticmethod
    def calculate_risk(activity):
        risk = float(activity.failed_logins * 10)
        if activity.request_count > ThreatEngine.RATE_LIMIT:
            risk += min((activity.request_count - ThreatEngine.RATE_LIMIT) * 2, 100)
        return risk

    @staticmethod
    def enforce(ip, score):
        if score < ThreatEngine.REQUEST_RISK_THRESHOLD:
            return

        BlockedIP.objects.update_or_create(
            ip_address=ip,
            defaults={
                "reason": "Suspicious traffic pattern detected",
                "blocked_until": timezone.now() + ThreatEngine.BLOCK_DURATION,
            },
        )


    @staticmethod
    def is_trusted(ip, user=None):
        if not ip:
            return False

        if user:
            return TrustedIP.objects.filter(ip_address=ip, user=user).exists()

        return TrustedIP.objects.filter(ip_address=ip).exists()
