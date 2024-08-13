from rest_framework import serializers
from .models import Scheduling
from datetime import datetime, timedelta

class SchedulingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduling
        fields = ['date', 'start_time', 'end_time', 'price', 'reference_until']

    def validate(self, data):
        now = datetime.now().time()
        today = datetime.today().date()

        if data['date'] == today and data['start_time'] <= now:
            raise serializers.ValidationError("Start time must be later than the current time for today.")

        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be later than start time.")

        start_datetime = datetime.combine(data['date'], data['start_time'])
        end_datetime = datetime.combine(data['date'], data['end_time'])
        if (end_datetime - start_datetime) < timedelta(minutes=30):
            raise serializers.ValidationError("End time must be at least 30 minutes after start time.")

        if not (1 <= data['price'] <= 1000):
            raise serializers.ValidationError("Price must be between 1 and 1000.")

        if data['reference_until'] < data['date']:
            raise serializers.ValidationError("Reference Until date must be on or after the start date.")

        return data


class ScheduledSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduling
        fields = '__all__'
