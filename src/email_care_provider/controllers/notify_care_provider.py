from datetime import datetime, date
from typing import Optional

from notifications_python_client.notifications import NotificationsAPIClient

from external_integrations.notify.settings import get_notify_settings
from internal_integrations.management_interface.api_client import (
    ManagementInterfaceApiClient,
)


class NotifyCareProviderController:
    def __init__(
        self,
        notifications_api_client: Optional[NotificationsAPIClient] = None,
        management_interface_api_client: Optional[ManagementInterfaceApiClient] = None,
    ):
        self.notifications_api_client = (
            notifications_api_client
            or NotificationsAPIClient(api_key=get_notify_settings().api_key)
        )
        self.management_interface_api_client = (
            management_interface_api_client or ManagementInterfaceApiClient()
        )

    def send_email_to_care_provider(
        self,
        *,
        patient_nhs_number: str,
        patient_given_name: str,
        patient_family_name: str,
        patient_birth_date: date,
        location_name: str,
        admitted_at: datetime
    ) -> None:
        notify_settings = get_notify_settings()
        care_provider = self.management_interface_api_client.get_care_provider(
            patient_nhs_number=patient_nhs_number
        )
        self.notifications_api_client.send_email_notification(
            email_address=care_provider.email,
            template_id=notify_settings.email_templates.ADMISSION,
            personalisation={
                "subj_given_name": patient_given_name,
                "subj_family_name": patient_family_name,
                "recp_given_name": care_provider.given_name,
                "subj_DOB": str(patient_birth_date),
                "event_loc": location_name,
                "event_time_str": str(admitted_at.date()),
                "event_date_str": str(admitted_at.time()),
            },
        )
