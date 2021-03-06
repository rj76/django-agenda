from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sitemaps import ping_google
from tinymce.models import HTMLField
from sorl.thumbnail import ImageField

from apps.core.widgets import LocationField

from .managers import EventManager


class Location(models.Model):
    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ('title',)
    
    def __unicode__(self):
        return self.title
        
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), db_index=True)
    location = LocationField(blank=True, max_length=255)
    address = models.CharField(_('address'), max_length=255, blank=True)


class Event(models.Model):
    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')
        ordering = ['-start_date', '-start_time', '-title']
        get_latest_by = 'start_date'
        permissions = (("change_author", ugettext("Change author")),)
        unique_together = ("start_date", "slug")

    def __unicode__(self):
        return _("%(title)s on %(start_date)s") % { 'title'      : self.title,
                                                    'start_date' : self.start_date }

    @models.permalink                                               
    def get_absolute_url(self):
        return ('events-detail', (), {
                  'year'  : self.start_date.year,
                  'month' : self.start_date.month,
                  'day'   : self.start_date.day,
                  'slug'  : self.slug })

    def get_picture(self):
        return self.image or 'default_comment.jpg'

    objects = EventManager()

    # Core fields
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), db_index=True)
    
    start_date = models.DateField(_('start date'))
    start_time = models.TimeField(_('start time'), blank=True, null=True)

    end_date = models.DateField(_('end date'))
    end_time = models.TimeField(_('end time'), blank=True, null=True)
    
    location = models.ForeignKey(Location, blank=True, null=True)

    image = ImageField(verbose_name=_('image'), upload_to='event_images', blank=True, null=True)

    short_description = models.TextField(_('short description'), null=False, blank=False)
    description = HTMLField(_('description'))

    calendar = models.ForeignKey("Calendar", blank=True, null=True, related_name='events')

    # Extra fields
    add_date = models.DateTimeField(_('add date'),auto_now_add=True)
    mod_date = models.DateTimeField(_('modification date'), auto_now=True)
    
    created_by = models.ForeignKey(User, verbose_name=_('created by'), db_index=True, blank=True, null=True)

    publish_date = models.DateTimeField(_('publication date'), default=datetime.now())
    publish = models.BooleanField(_('publish'), default=True)
    
    allow_comments = models.BooleanField(_('Allow comments'), default=True)

    def save(self):
        super(Event, self).save()
        if not settings.DEBUG:
            try:
                ping_google()
            except Exception:
                import logging
                logging.warn('Google ping on save did not work.')


class EventUsers(models.Model):

    class Meta:
        ordering = ['-created']

    CHOICES = (
        (_('no'), _('No')),
        (_('maybe'), _('Maybe')),
        (_('going'), _('Going')),
    )

    event = models.ForeignKey(Event, related_name="users")
    user = models.ForeignKey(User, related_name="events")
    rsvp = models.CharField(_('RSVP'), choices=CHOICES, blank=False, null=False, max_length=10)
    created = models.DateTimeField(_('add date'),auto_now_add=True)


class TitleAbstractBase(models.Model):
    """ Abstract base class adding a title field. """
    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title

    title = models.CharField(max_length=255, verbose_name=_('title'))


class EventImage(TitleAbstractBase):
    """ Image related to an event. """
    event = models.ForeignKey(Event)
    image = ImageField(verbose_name=_('image'), upload_to='event_images')


class EventFile(TitleAbstractBase):
    """ File related to an event. """
    event = models.ForeignKey(Event)
    file = models.FileField(verbose_name=_('file'), upload_to='event_files')


class Calendar(models.Model):
    name = models.CharField(_('name'), max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = _('calendar')
        verbose_name_plural = _('calendars')

    def __unicode__(self):
        if self.name:
            return self.name

