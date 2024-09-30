from rest_framework import serializers
from .models import Scheduling,LawyerProfile,BookedAppointment,PaymentDetails
from api.models import CustomUser
from datetime import datetime, timedelta

class SchedulingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduling
        fields = ['date', 'start_time', 'end_time', 'price']

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
    
        # if data['reference_until'] < data['date']:
        #     raise serializers.ValidationError("Reference Until date must be on or after the start date.")

        return data


class ScheduledSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduling
        fields = '__all__'


class SheduledSerilizerForUserSide(serializers.ModelSerializer):
    class Meta:
        model = Scheduling
        fields = ['id','start_time', 'end_time', 'price']  

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'profile_image']


class LawyerProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = LawyerProfile
        fields = ['user']
        
class SchedulingSerializerForScheduledSession(serializers.ModelSerializer):
    lawyer_profile = LawyerProfileSerializer()

    class Meta:
        model = Scheduling
        fields = ['start_time', 'end_time', 'lawyer_profile']

class BookedAppointmentSerializer(serializers.ModelSerializer):
    scheduling = SchedulingSerializerForScheduledSession()
    session_start = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    session_end = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    user_profile =CustomUserSerializer()
    class Meta:
        model = BookedAppointment
        fields = ['uuid', 'session_start','session_end', 'scheduling', 'booked_at','user_profile']
        # fields = ['uuid', 'session_date', 'scheduling', 'booked_at','user_profile']


class SchedulingSerializerForAdmin(serializers.ModelSerializer):
    lawyer_profile = LawyerProfileSerializer()
    class Meta:
        model = Scheduling
        fields = ['id', 'date', 'start_time', 'end_time', 'price', 'lawyer_profile','is_listed']


class PaymentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentDetails
        fields = '__all__'

class BookedAppointmentSerializerForSalesReport(serializers.ModelSerializer):
    payment_details = PaymentDetailsSerializer()
    scheduling = SchedulingSerializerForAdmin()
    user_profile= CustomUserSerializer()

    class Meta:
        model= BookedAppointment
        fields = '__all__'