# apps/security/api/v1/serializers.py

from rest_framework import serializers
from apps.security.models import BlockedIP, TrustedIP


class BlockedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockedIP
        fields = "__all__"


class TrustedIPSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrustedIP
        fields = "__all__"