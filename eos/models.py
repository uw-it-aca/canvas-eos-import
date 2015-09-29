from django.db import models


class EOSCourseDeltaManager(models.Manager):
    def queued(self, queue_id):
        return super(EOSCourseDeltaManager, self).get_query_set().filter(
            queue_id=queue_id)

    def dequeue(self, queue_id, provisioned_date=None):
        if provisioned_date is not None:
            self.queued(queue_id).update(
                queue_id=None, provisioned_date=provisioned_date)
        else:
            self.queued(queue_id).delete()
    

class EOSCourseDelta(models.Model):
    queue_id = models.CharField(max_length=30, null=True)
    term_id = models.CharField(max_length=20)
    changed_since_date = models.DateTimeField()
    query_date = models.DateTimeField()
    provisioned_date = models.DateTimeField(null=True)

    objects = EOSCourseDeltaManager()

    class Meta:
        get_latest_by = 'query_date'
