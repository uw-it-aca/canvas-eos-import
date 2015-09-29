from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import mail_admins
from django.utils.log import getLogger
from django.utils.timezone import utc
from restclients.sws.term import get_term_by_year_and_quarter
from restclients.models.sws import Section
from restclients.exceptions import DataFailureException
from sis_provisioner.models import SubAccountOverride, Import
from sis_provisioner.pidfile import Pidfile, ProcessRunningException
from eos.models import EOSCourseDelta
from eos.client import EOS
from eos.csv_builder import EOSCSVBuilder
from optparse import make_option
from datetime import datetime, timedelta
import re
import traceback


logger = getLogger('sis_provisioner')

QUARTER_DEFAULT = 'autumn'
YEAR_DEFAULT = '2015'


class Command(BaseCommand):
    help = "Poll EOS for course and instructor delta"

    option_list = BaseCommand.option_list + (
        make_option('--registrations', dest='registrations', default=None, help='include course registrations'),
        make_option('--quarter', dest='quarter', default=QUARTER_DEFAULT, help='autumn, winter, spring or summer, default "%s"' % QUARTER_DEFAULT),
        make_option('--year', dest='year', default=YEAR_DEFAULT, help='four digit year, default "%s"' % YEAR_DEFAULT),
        make_option('--delta', dest='delta', default=None, help='import changes since, e.g., 30m or 2h or 5d or import'),
    )

    def handle(self, *args, **options):
        try:
            self._options = options

            with Pidfile(logger=logger):
                term = get_term_by_year_and_quarter(int(options['year']), options['quarter'])

                self.now = datetime.utcnow().replace(tzinfo=utc)
                if options['delta']:
                    if options['delta'] == 'import':
                        term_id = term.canvas_sis_id()
                        delta = EOSCourseDelta.objects.filter(term_id=term_id).latest()
                        if delta.provisioned_date:
                            changed_since_dt = delta.query_date
                        else:
                            complaint = "EOS import abort: previous import of %s not finished" % (term_id)
                            logger.info(complaint)
                            return
                    else:
                        match = re.match(r'^(\d+)([smhdw])$', options['delta'])
                        if match:
                            offset = {
                                {
                                    'w': 'weeks',
                                    'd': 'days',
                                    'h': 'hours',
                                    'm': 'minutes',
                                    's': 'seconds'
                                }[match.group(2)] : int(match.group(1))
                            }

                            changed_since_dt = self.now - timedelta(**offset)
                        else:
                            logger.error("unknown delta: %s" % options['delta'])
                            return
                else:
                    changed_since_dt = None

                self.gather_and_import(term, changed_since_dt)
        except ProcessRunningException as err:
            logger.info('import_eos_courses exit: %s' % err)
        except EOSCourseDelta.DoesNotExist:
            logger.error("no model for previous import")

    def gather_courses(self, term, changed_since_dt):
        courses = EOS().get_courses_changed_since(term, changed_since_dt)
        import_courses = []
        for course in courses:
            course_id = course.canvas_course_sis_id()
            subaccount_id = settings.LMS_OWNERSHIP_SUBACCOUNT.get(
                course.lms_ownership, None)

            if course.primary_lms and course.primary_lms != Section.LMS_CANVAS:
                subaccount_id = 'NONE'

            try:
                override = SubAccountOverride.objects.get(course_id=course_id)

                if course.is_withdrawn and course.is_credit:
                    override.delete()
                    continue
                else:
                    import_courses.append(course)
                    if subaccount_id is not None:
                        if subaccount_id != override.subaccount_id:
                            override.subaccount_id = subaccount_id
                            override.save()
                    else:
                        override.delete()
            except SubAccountOverride.DoesNotExist:
                if course.is_withdrawn and course.is_credit:
                    continue
                else:
                    import_courses.append(course)
                    if subaccount_id is not None:
                        override = SubAccountOverride(
                            course_id=course_id, subaccount_id=subaccount_id)
                        override.save()

        return import_courses

    def gather_registrations(self, term, changed_since_dt):
        return EOS().get_registrations_changed_since(term, changed_since_dt)

    def gather_and_import(self, term, changed_since_dt):
        imp = Import(priority=1, csv_type='eoscourse')
        try:
            import_courses = self.gather_courses(term, changed_since_dt)
            import_registrations = self.gather_registrations(term, changed_since_dt) if self._options['registrations'] else []
        except:
            imp.csv_errors = traceback.format_exc()
            imp.save()
            return

        if (not len(import_courses) and not len(import_registrations)):
            return

        imp.save()
        try:
            imp.csv_path = EOSCSVBuilder().generate_csv(
                sections=import_courses, registrations=import_registrations)
        except:
            imp.csv_errors = traceback.format_exc()

        imp.save()

        if imp.csv_path:

            EOSCourseDelta.objects.create(
                queue_id=imp.pk,
                changed_since_date=changed_since_dt if changed_since_dt else datetime(1970,1,1).replace(tzinfo=utc),
                term_id=term.canvas_sis_id(),
                query_date=self.now)

            imp.import_csv()
        elif not imp.csv_errors:
            imp.delete()
