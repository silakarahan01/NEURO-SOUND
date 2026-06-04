from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    ContactMessage,
    ListeningLog,
    MusicTrack,
    Notification,
    Prescription,
    SessionNote,
    SubscriptionPlan,
    SurveyResponse,
    User,
    UserSubscription,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_psychologist', 'is_individual', 'is_active']
    list_filter = ['is_psychologist', 'is_individual', 'is_staff', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = UserAdmin.fieldsets + (
        ('Özel Bilgiler (Proje Bazlı)', {
            'fields': (
                'is_psychologist', 'is_individual',
                'verification_code', 'verification_code_expires_at',
                'assigned_psychologist',
                'description', 'psychologist_notes',
                'phone_number', 'birth_date',
            ),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Özel Bilgiler (Proje Bazlı)', {
            'fields': (
                'is_psychologist', 'is_individual',
                'verification_code', 'verification_code_expires_at',
                'assigned_psychologist',
                'phone_number', 'birth_date',
            ),
        }),
    )


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'assigned_by', 'frequency', 'duration_minutes', 'total_days', 'created_at', 'notes']
    list_filter = ['frequency', 'created_at']
    search_fields = ['patient__username', 'assigned_by__username']
    readonly_fields = ['created_at']


@admin.register(ListeningLog)
class ListeningLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'frequency', 'duration_listened', 'is_completed']
    list_filter = ['is_completed', 'date', 'frequency']
    search_fields = ['user__username']


@admin.register(SessionNote)
class SessionNoteAdmin(admin.ModelAdmin):
    list_display = ['patient', 'created_by', 'date', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['patient__username', 'created_by__username']
    readonly_fields = ['created_at']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'created_at']
    readonly_fields = ['created_at']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'plan', 'end_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['name', 'email', 'message', 'created_at']
    list_editable = ['is_read']
    ordering = ['-created_at']


@admin.register(MusicTrack)
class MusicTrackAdmin(admin.ModelAdmin):
    list_display = ['title', 'icon', 'color', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'icon', 'color']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at']
    ordering = ['order', 'title']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_read']
    ordering = ['-created_at']


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'recommended_frequency', 'recommended_minutes',
        'ml_confidence', 'plan_start_date', 'plan_expires_at', 'renewal_notified', 'created_at',
    ]
    list_filter = ['recommended_frequency', 'plan_start_date', 'renewal_notified']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'user', 'sleep_quality', 'stress_level', 'focus_level',
        'mood_score', 'anxiety_level', 'fatigue_level',
        'recommended_frequency', 'recommended_minutes', 'ml_confidence',
        'plan_start_date', 'plan_expires_at', 'renewal_notified', 'created_at',
    ]
    ordering = ['-created_at']
