from rest_framework import serializers

class ReportCreateRequestSerializer(serializers.Serializer):
    reported_user_id = serializers.IntegerField()
    reason = serializers.CharField(min_length=1, max_length=2000)

class ReportCreateResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()
    report_id = serializers.IntegerField()
