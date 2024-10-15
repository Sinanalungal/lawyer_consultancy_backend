from django.db.models import Count
from django.utils.timezone import now, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import CustomUser
from django.db.models import Sum, F, Q, ExpressionWrapper, FloatField
from schedule.models import BookedAppointment
from case.models import AllotedCases
from server.permissions import VerifiedUser, IsAdmin, IsLawyer
from datetime import datetime
from django.db.models.functions import ExtractMonth


class UserGrowthView(APIView):
    """
    API view to retrieve user growth statistics for the past 12 months.

    Returns:
        Response: JSON response with user and lawyer counts, monthly growth, revenue, completed sessions, and top lawyers.
    """
    permission_classes = [IsAdmin, VerifiedUser]

    def get(self, request, *args, **kwargs):
        """
        Handle GET request for user growth data.

        Args:
            request: The request object.

        Returns:
            Response: User growth statistics in JSON format.
        """

        total_users = CustomUser.objects.count()
        total_lawyers = CustomUser.objects.filter(role='lawyer').count()
        non_canceled_appointments = BookedAppointment.objects.filter(
            Q(is_canceled=False) & Q(is_completed=True))

        months = []
        user_growth = []
        lawyer_growth = []

        for i in range(12):
            month = now() - timedelta(days=30 * (11 - i))
            months.append(month.strftime("%B"))

            users_count = CustomUser.objects.filter(
                role='user', created_at__year=month.year, created_at__month=month.month
            ).count()
            lawyers_count = CustomUser.objects.filter(
                role='lawyer', created_at__year=month.year, created_at__month=month.month
            ).count()

            user_growth.append(users_count)
            lawyer_growth.append(lawyers_count)

        appointments_with_amount = non_canceled_appointments.annotate(
            amount_10_percent=ExpressionWrapper(
                F('scheduling__price') * 0.1, output_field=FloatField())
        )

        total_completed_sessions = non_canceled_appointments.count()
        total_amount = appointments_with_amount.aggregate(
            total_sum=Sum('amount_10_percent'))['total_sum']

        # print(total_amount)
        top_lawyers = non_canceled_appointments.values('scheduling__lawyer_profile__user__full_name').annotate(
            completed_sessions=Count('id')
        ).order_by('-completed_sessions')[:5]

        return Response({
            "total_users": total_users-1,
            "total_lawyers": total_lawyers,
            "months": months,
            "user_growth": user_growth,
            "lawyer_growth": lawyer_growth,
            "total_revenue": total_amount if total_amount else 0,
            'total_completed_sessions': total_completed_sessions,
            'top_lawyers': top_lawyers,
        })


class LawyerDashboardView(APIView):
    """
    API view to provide lawyer-specific statistics and data.

    Returns:
        Response: JSON response with completed cases, revenue, sessions, and monthly statistics.
    """
    permission_classes = [IsLawyer, VerifiedUser]

    def get(self, request, *args, **kwargs):
        """
        Handle GET request for lawyer dashboard data.

        Args:
            request: The request object.

        Returns:
            Response: Lawyer-specific statistics in JSON format.
        """
        try:
            non_canceled_appointments = BookedAppointment.objects.filter(
                Q(is_canceled=False) & Q(is_completed=True) & Q(
                    scheduling__lawyer_profile__user=request.user)
            )
            lawyer_cases = AllotedCases.objects.filter(
                Q(status='Completed') & Q(
                    selected_case__lawyer__user=request.user)
            )
            lawyer_cases_count = lawyer_cases.count()
        except:
            return Response({"error": "There is no such lawyer."}, status=404)

        lawyer_profile = request.user.lawyer_profile
        current_year = datetime.now().year

        attended_cases = (
            lawyer_cases
            .filter(created_at__year=current_year)
            .annotate(month=ExtractMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        booked_sessions = (
            BookedAppointment.objects.filter(
                Q(scheduling__lawyer_profile=lawyer_profile) & Q(is_completed=True))
            .filter(session_start__year=current_year)
            .annotate(month=ExtractMonth('session_start'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        sessions_count = [0] * 12
        cases_count = [0] * 12

        for session in booked_sessions:
            sessions_count[session['month'] - 1] = session['count']

        for session in attended_cases:
            cases_count[session['month'] - 1] = session['count']

        appointments_with_amount = non_canceled_appointments.annotate(
            amount_80_percent=ExpressionWrapper(
                F('scheduling__price') * 0.8, output_field=FloatField())
        )

        total_completed_sessions = non_canceled_appointments.count()
        total_amount = appointments_with_amount.aggregate(
            total_sum=Sum('amount_80_percent'))['total_sum']

        return Response({
            "total_completed_cases": lawyer_cases_count,
            "total_revenue": total_amount if total_amount else 0,
            'total_completed_sessions': total_completed_sessions,
            'months': months,
            'sessions_count': sessions_count,
            'case_count': cases_count,
        })
