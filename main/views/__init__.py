# main/views/__init__.py
# Tüm view'ları tek noktadan dışa aktarır (backward compatibility).

from .auth import (
    login_view, register_view, logout_view, profile_view,
    verify_email_view, resend_verification_view,
)
from .public import (
    landing_view, cookie_policy_view, frequency_info_view,
    contact_view, kvkk_view, terms_view, privacy_view,
)
from .patient import patient_dashboard, music_library, payment_view, survey_view
from .psychologist import (
    psychologist_dashboard, delete_prescription, patient_detail_view,
    prescription_update_view, delete_session_note_view,
)
from .admin import (
    super_admin_dashboard, admin_onaylar_view, admin_formlar_view,
    admin_patients_view, admin_psychologists_view, admin_patient_detail_view,
    send_verification_code, approve_psychologist, delete_user,
    mark_message_read, admin_muzik_view,
)
from .api import save_progress, mark_notification_read, mark_all_notifications_read

__all__ = [
    'login_view', 'register_view', 'logout_view', 'profile_view',
    'verify_email_view', 'resend_verification_view',
    'landing_view', 'cookie_policy_view', 'frequency_info_view',
    'contact_view', 'kvkk_view', 'terms_view', 'privacy_view',
    'patient_dashboard', 'music_library', 'payment_view', 'survey_view',
    'psychologist_dashboard', 'delete_prescription', 'patient_detail_view',
    'prescription_update_view', 'delete_session_note_view',
    'super_admin_dashboard', 'admin_onaylar_view', 'admin_formlar_view',
    'admin_patients_view', 'admin_psychologists_view', 'admin_patient_detail_view',
    'send_verification_code', 'approve_psychologist', 'delete_user',
    'mark_message_read', 'admin_muzik_view',
    'save_progress', 'mark_notification_read', 'mark_all_notifications_read',
]
