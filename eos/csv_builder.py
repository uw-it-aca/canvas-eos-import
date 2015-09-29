from sis_provisioner.csv_builder import CSVBuilder
from sis_provisioner.csv_formatters import csv_for_enrollment
from sis_provisioner.models import Enrollment


class EOSCSVBuilder(CSVBuilder):

    def generate_csv(self, sections=[], registrations=[]):
        for section in sections:
            self.generate_primary_section_csv(section, include_enrollment=False)

        for registration in registrations:
            self.generate_user_csv_for_person(registration.person, force=True)

            if registration.person.uwregid not in self._invalid_users:
                section_id = registration.section.canvas_section_sis_id()
                status = Enrollment.ACTIVE_STATUS if (
                    registration.is_active) else Enrollment.DELETED_STATUS
                csv_data = csv_for_enrollment(section_id, registration.person,
                                              self.STUDENT_ROLE, status)
                self._csv.add_enrollment(csv_data)

        return self._csv.write_files()

    def generate_student_enrollment_csv(self, section):
        """EOS enrollments are sourced from outside SWS
        """
        return

    def generate_xlists_csv(self, section):
        """EOS never returns joint information
        """
        return
