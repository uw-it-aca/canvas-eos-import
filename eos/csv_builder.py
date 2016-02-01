from sis_provisioner.csv_builder import CSVBuilder
from sis_provisioner.csv_formatters import csv_for_sis_student_enrollment


class EOSCSVBuilder(CSVBuilder):

    def generate_csv(self, sections=[], registrations=[]):
        self._include_enrollment = False
        for section in sections:
            self.generate_primary_section_csv(section)

        for registration in registrations:
            self.generate_user_csv_for_person(registration.person, force=True)

            if registration.person.uwregid not in self._invalid_users:
                csv_data = csv_for_sis_student_enrollment(registration)
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
