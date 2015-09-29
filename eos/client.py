from django.conf import settings
from django.utils.log import getLogger
from django.utils.timezone import localtime
from restclients.dao_implementation.live import get_con_pool, get_live_url
from restclients.dao_implementation.mock import get_mockdata_url
from restclients.exceptions import DataFailureException
from restclients.models.sws import Term, Section, SectionMeeting, Registration
from restclients.pws import PWS
from sis_provisioner.csv_data import CSVData
from sis_provisioner.models import Course, TermOverride
from urllib import urlencode
from lxml import etree
import os


class PrimaryEnrollmentException(Exception):
    pass


class EOS_DAO(object):
    pool = None

    def getURL(self, url, headers):
        eos_host = getattr(settings, 'RESTCLIENTS_EOS_HOST', None)
        if eos_host:
            if EOS_DAO.pool is None:
                EOS_DAO.pool = get_con_pool(eos_host)

            return get_live_url(EOS_DAO.pool, 'GET', eos_host, url,
                                headers=headers, service_name='eos')

        return get_mockdata_url('eos', 'file', url, headers)


class EOS(object):
    def __init__(self):
        self._log = getLogger('sis_provisioner')

    def _get_resource(self, url):
        response = EOS_DAO().getURL(url, {'Accept': 'application/xhtml+xml'})

        if response.status != 200:
            raise DataFailureException(url, response.status, response.data)

        try:
            xml_response = etree.fromstring(response.data)
            self._stash(url, response.data)
            return xml_response
        except etree.XMLSyntaxError:
            return etree.Element('root')

    def _eos_section(self):
        section = Section()
        section.is_primary_section = True
        section.is_independent_study = False
        section.linked_section_urls = []
        section.joint_section_urls = []

        section_meeting = SectionMeeting()
        section_meeting.instructors = []
        section.meetings = [section_meeting]

        return section

    def get_courses_changed_since(self, term, since_dt):
        url = '/uweomyuw/feed/courseSectionWS.asp'
        params = {'year': term.year, 'quarter': term.quarter.lower(),
                  'resultSetOption': 1}

        if since_dt:
            since_dt = localtime(since_dt)
            params['last_modified_date'] = since_dt.strftime('%m/%d/%Y %H:%M')

        xml_root = self._get_resource('%s?%s' % (url, urlencode(params)))

        courses = {}
        for el in xml_root.findall('row'):
            section = self._eos_section()
            section.term = term
            section.eos_course_id = el.find('EOScourseId').text.strip()
            section.curriculum_abbr = el.find(
                'CurriculumAbbreviation').text.strip()
            section.course_number = el.find('CourseNumber').text.strip()
            section.section_id = el.find('SectionID').text.strip()
            section.course_campus = el.find('CourseCampus').text.strip()

            course_title = el.find('CourseTitle')
            if course_title is not None:
                section.course_title = course_title.text.strip()
            course_title_long = el.find('CourseTitleLong')
            if course_title_long is not None:
                section.course_title_long = course_title_long.text.strip()

            primary_lms = el.find('primaryLMS')
            if primary_lms is not None:
                section.primary_lms =  primary_lms.text.strip()
            lms_ownership = el.find('LMSOwnership')
            section.lms_ownership = None if (
                lms_ownership is None) else lms_ownership.text.strip()

            section.delete_flag = el.find('DeleteFlag').text.strip()
            section.is_withdrawn = True if (
                'withdrawn' == section.delete_flag) else False

            is_independent_start = el.find('IsIndependentStart')
            section.is_independent_start = True if (
                is_independent_start is not None and
                is_independent_start.text.strip() == '1') else False

            course_id = section.canvas_course_sis_id()
            try:
                override = TermOverride.objects.get(course_id=course_id)
                if not section.is_independent_start:
                    override.delete()
            except TermOverride.DoesNotExist:
                if section.is_independent_start:
                    override = TermOverride(
                        course_id=course_id,
                        term_sis_id="uweo-individual-start",
                        term_name="UWEO Individual Start"
                    )
                    override.save()
                    
            is_credit = el.find('is_credit')
            section.is_credit = True if (
                is_credit is not None and
                is_credit.text.strip() == '1') else False

            courses[section.eos_course_id] = section

        # Get the instructors
        params['resultSetOption'] = 2
        xml_root = self._get_resource('%s?%s' % (url, urlencode(params)))

        pws = PWS()
        for el in xml_root.findall('row'):
            eos_course_id = el.find('EOScourseId').text.strip()
            course = courses[eos_course_id]

            employee_id = el.find('EmployeeID').text.strip()
            try:
                person = pws.get_person_by_employee_id(employee_id)
                course.meetings[0].instructors.append(person)
            except DataFailureException as ex:
                self._log.info('Skipping employee_id %s: %s' % (
                    employee_id, ex))
                continue

        return courses.values()

    def get_registrations_changed_since(self, term, since_dt):
        url = '/uweomyuw/feed/registrationWS.asp'
        params = {'year': term.year, 'quarter': term.quarter.lower()}

        if since_dt:
            since_dt = localtime(since_dt)
            params['last_modified_date'] = since_dt.strftime('%m/%d/%Y %H:%M')

        xml_root = self._get_resource('%s?%s' % (url, urlencode(params)))

        registrations = []
        pws = PWS()
        for el in xml_root.findall('row'):
            registration = Registration()
            student_number = el.find('student_number').text.strip()
            try:
                person = pws.get_person_by_student_number(student_number)
                registration.person = person
            except DataFailureException as ex:
                self._log.info('Skipping student_number %s: %s' % (
                    student_number, ex))
                continue

            section = self._eos_section()
            section.term = Term(
                year=int(el.find('year').text.strip()),
                quarter=el.find('quarter').text.strip().lower()
            )
            section.curriculum_abbr = el.find(
                'curriculum_abbreviation').text.strip()
            section.course_number = el.find('course_number').text.strip()
            section.section_id = el.find('section_id').text.strip()
            registration.section = section

            is_credit = el.find('is_credit')
            registration.is_credit = True if (
                is_credit is not None and
                is_credit.text.strip() == '1') else False

            if registration.is_credit:
                try:
                    self._update_is_primary(section)
                except PrimaryEnrollmentException as err:
                    self._log.info('Skipping registration for %s: %s' % (
                        student_number, err))
                    continue

            registration.request_status = el.find(
                'request_status').text.strip().lower()

            is_active = el.find('is_active')
            registration.is_active = True if (
                is_active is not None and
                is_active.text.strip() == '1') else False

            is_deleted = el.find('is_deleted')
            if (is_deleted is not None and is_deleted.text.strip() == '1'):
                    registration.is_active = False

            registrations.append(registration)

        return registrations

    def _update_is_primary(self, section):
        try:
            course_id = section.canvas_course_sis_id()
            course = Course.objects.get(course_id=course_id)
            if course.primary_id:
                section.is_primary_section = False
            else:
                section.is_primary_section = True
                secondaries = Course.objects.filter(primary_id=course_id)
                if len(secondaries):
                    raise PrimaryEnrollmentException('primary section %s' % course_id)
        except Course.DoesNotExist:
            raise PrimaryEnrollmentException('unknown course %s' % course_id)

    def _stash(self, url, data):
        root = os.path.normpath(os.path.join(settings.SIS_IMPORT_CSV_ROOT, '../eos'))
        filepath = CSVData().filepath(root=root)
        filename = os.path.join(filepath, 'response')
        f = open(filename, 'w')
        f.write('%s\n' % url)
        f.write(data)
        f.close()

