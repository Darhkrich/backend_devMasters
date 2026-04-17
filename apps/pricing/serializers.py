from rest_framework import serializers
from .models import Package, BuilderOption, BuilderPriority

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"

class BuilderOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuilderOption
        fields = "__all__"

class BuilderPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = BuilderPriority
        fields = "__all__"