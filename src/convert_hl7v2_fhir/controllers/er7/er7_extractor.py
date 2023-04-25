from datetime import datetime, timezone
from typing import List
import hl7apy
from hl7apy.core import Message

from convert_hl7v2_fhir.controllers.er7.exceptions import (
    MissingNHSNumberError,
    InvalidNHSNumberError,
    MissingPointOfCareError,
    MissingFacilityError,
    MissingPatientClassError,
    MissingAdmissionTypeError,
    MissingTimeOfAdmissionError,
    MissingFamilyNameError,
    MissingGivenNameError,
)
from convert_hl7v2_fhir.controllers.utils import is_nhs_number_valid


class ER7Extractor:
    def __init__(self, er7_message: Message):
        self.er7_message = er7_message

    def nhs_number(self) -> str:
        """There are two potential fields where NHS number can be:
        1. PID.2 - Patient Id
        2. PID.3 - Patient Identifier List"""

        nhs_numbers = [
            composite_id.id.value
            for composite_id in self.er7_message.pid.patient_id_internal_id
            if "NHSNMBR" in composite_id.value
        ]
        if "NHSNMBR" in self.er7_message.pid.patient_id_external_id.value:
            nhs_numbers.append(self.er7_message.pid.patient_id_external_id.id.value)

        if not nhs_numbers:
            raise MissingNHSNumberError

        try:
            return next(
                (
                    nhs_number
                    for nhs_number in nhs_numbers
                    if is_nhs_number_valid(nhs_number)
                )
            )
        except StopIteration:
            raise InvalidNHSNumberError

    def family_name(self) -> str:
        _family_name = self.er7_message.pid.patient_name.family_name.value
        if not _family_name:
            raise MissingFamilyNameError

        return self.er7_message.pid.patient_name.family_name.value

    def given_name(self) -> List[str]:
        _names = [self.er7_message.pid.patient_name.given_name.value]
        if all(not n for n in _names):
            raise MissingGivenNameError

        _names.extend(
            self.er7_message.pid.patient_name.middle_initial_or_name.value.split()
        )
        return [name.strip() for name in _names]

    def date_of_birth(self) -> datetime:
        _dob = self.er7_message.pid.date_of_birth.value
        date_of_birth, _, utc_offset, _ = hl7apy.utils.get_datetime_info(_dob)
        if not utc_offset:
            return date_of_birth.replace(tzinfo=timezone.utc)

        return date_of_birth.replace(tzinfo=datetime.strptime(utc_offset, "%z").tzinfo)

    def event_type_code(self) -> str:
        return self.er7_message.evn.event_type_code.value

    def patient_location(self) -> str:
        _poc = self.er7_message.pv1.assigned_patient_location.point_of_care_id.value
        if not _poc:
            raise MissingPointOfCareError

        _facility = self.er7_message.pv1.assigned_patient_location.facility_hd.value
        if not _facility:
            raise MissingFacilityError

        return f"{_poc}, {_facility}"

    def patient_class(self) -> str:
        _patient_class = self.er7_message.pv1.patient_class.value
        if not _patient_class:
            raise MissingPatientClassError

        return self.er7_message.pv1.patient_class.value

    def admission_type(self) -> str:
        _admission_type = self.er7_message.pv1.admission_type.value
        if not _admission_type:
            raise MissingAdmissionTypeError

        return self.er7_message.pv1.admission_type.value

    def time_of_admission(self) -> datetime:
        _toa = self.er7_message.pv1.admit_date_time.value
        if not _toa:
            raise MissingTimeOfAdmissionError

        time_of_admission, _, utc_offset, _ = hl7apy.utils.get_datetime_info(_toa)
        if not utc_offset:
            return time_of_admission.replace(tzinfo=timezone.utc)

        return time_of_admission.replace(
            tzinfo=datetime.strptime(utc_offset, "%z").tzinfo
        )