"""Course content and durable student records.
Copyright (c) 2026 Min SiThu (devminsithu). SPDX-License-Identifier: MIT
"""
import hashlib
import json
import re
import uuid
from urllib.parse import urlparse, parse_qs
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


def video_embed_url(url):
    if not url:
        return ''
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        return ''
    host = (parsed.hostname or '').lower()
    video_id = ''
    if host in ('youtube.com','www.youtube.com','m.youtube.com'):
        if parsed.path == '/watch':
            video_id = parse_qs(parsed.query).get('v',[''])[0]
        elif parsed.path.startswith('/embed/'):
            video_id = parsed.path.split('/')[2]
    elif host == 'youtu.be':
        video_id = parsed.path.strip('/')
    if re.fullmatch(r'[A-Za-z0-9_-]{11}',video_id):
        return f'https://www.youtube-nocookie.com/embed/{video_id}'
    if host in ('vimeo.com','www.vimeo.com','player.vimeo.com'):
        video_id = parsed.path.rstrip('/').split('/')[-1]
        if re.fullmatch(r'\d{5,12}',video_id):
            return f'https://player.vimeo.com/video/{video_id}'
    return ''


class Course(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=240)
    description = models.TextField()
    category = models.CharField(max_length=60, default='Technology')
    level = models.CharField(max_length=20, choices=[('Beginner','Beginner'),('Intermediate','Intermediate'),('Advanced','Advanced')], default='Beginner')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='taught_courses')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=[('MMK','MMK'),('USD','USD'),('THB','THB')], default='MMK')
    published = models.BooleanField(default=False)
    accent = models.CharField(max_length=10,choices=[('teal','Teal'),('coral','Coral'),('blue','Blue')],default='teal')
    pass_percentage = models.PositiveSmallIntegerField(default=80,validators=[MinValueValidator(1),MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self): return self.title
    @property
    def duration_minutes(self): return sum(self.lessons.values_list('minutes',flat=True))
    def quiz_signature(self):
        data = [self.pass_percentage,list(self.questions.order_by('position','id').values_list('id','prompt','option_a','option_b','option_c','option_d','correct'))]
        return hashlib.sha256(json.dumps(data).encode()).hexdigest()


class Lesson(models.Model):
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name='lessons')
    title = models.CharField(max_length=160)
    position = models.PositiveIntegerField(default=1)
    minutes = models.PositiveSmallIntegerField(default=10,validators=[MinValueValidator(1)])
    content = models.TextField(help_text='Plain text. Separate paragraphs with blank lines. HTML is escaped.')
    video_url = models.URLField(blank=True,help_text='Optional HTTPS YouTube or Vimeo URL. Only embed videos you own or may use.')
    class Meta:
        ordering = ['position','id']
    def __str__(self): return f'{self.course}: {self.title}'
    def clean(self):
        if self.video_url and not video_embed_url(self.video_url):
            raise ValidationError({'video_url':'Use a valid HTTPS YouTube or Vimeo video link.'})
    @property
    def embed_url(self): return video_embed_url(self.video_url)


class Question(models.Model):
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name='questions')
    position = models.PositiveIntegerField(default=1)
    prompt = models.CharField(max_length=500)
    option_a = models.CharField(max_length=240)
    option_b = models.CharField(max_length=240)
    option_c = models.CharField(max_length=240)
    option_d = models.CharField(max_length=240)
    correct = models.PositiveSmallIntegerField(choices=[(1,'A'),(2,'B'),(3,'C'),(4,'D')],default=1)
    class Meta:
        ordering = ['position','id']
    def __str__(self): return self.prompt
    @property
    def options(self): return enumerate([self.option_a,self.option_b,self.option_c,self.option_d],start=1)


class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='enrollments')
    course = models.ForeignKey(Course,on_delete=models.CASCADE,related_name='enrollments')
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','course'],name='one_enrollment')]
        ordering = ['-joined_at']
    def __str__(self): return f'{self.student} — {self.course}'


class Completion(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson,on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','lesson'],name='one_completion')]


class Attempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    course = models.ForeignKey(Course,on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()
    passed = models.BooleanField()
    quiz_signature = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    course = models.ForeignKey(Course,on_delete=models.PROTECT)
    student_name = models.CharField(max_length=160)
    course_title = models.CharField(max_length=160)
    issued_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','course'],name='one_certificate')]
        ordering = ['-issued_at']


def private_upload(instance, filename):
    return f'payments/{uuid.uuid4().hex}'

class PaymentMethod(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=80)
    currency = models.CharField(max_length=3, default='MMK', choices=[('MMK','MMK'),('USD','USD'),('THB','THB')])
    instructions = models.TextField(help_text='Merchant account name, account number and transfer instructions. Never enter passwords.')
    qr = models.ImageField(upload_to=private_upload, blank=True)
    enabled = models.BooleanField(default=False)
    def __str__(self): return self.name
    def clean(self):
        if self.enabled and not self.instructions.strip():
            raise ValidationError({'instructions':'Add real merchant details before enabling.'})

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    method = models.ForeignKey(PaymentMethod, null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, default='pending', choices=[('pending','Awaiting payment'),('submitted','Under review'),('paid','Paid'),('rejected','Rejected')])
    reference = models.CharField(max_length=120, blank=True)
    receipt = models.ImageField(upload_to=private_upload, blank=True)
    stripe_session = models.CharField(max_length=255, blank=True, unique=True, null=True)
    review_note = models.CharField(max_length=500, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='reviewed_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self): return f'{self.id} · {self.status}'
