"""Behavior and authorization regression tests. Min SiThu (devminsithu), MIT."""
import hashlib
import hmac
import io
import json
import tempfile
import time
from decimal import Decimal
from unittest.mock import patch
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from .models import Course, Lesson, Question, Enrollment, Completion, Attempt, Certificate, Order, PaymentMethod, video_embed_url

class LearningTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_superuser('owner','owner@example.com','owner-pass-987!')
        self.student=User.objects.create_user('learner',password='learner-pass-987!')
        self.other=User.objects.create_user('other',password='other-pass-987!')
        self.teacher=User.objects.create_user('teacher',is_staff=True)
        self.course=Course.objects.create(title='Original course',slug='original',summary='Learn',description='Original text',instructor=self.owner,published=True)
        self.lesson=Lesson.objects.create(course=self.course,title='Start',content='Learn something.')
        self.question=Question.objects.create(course=self.course,prompt='Which answer?',option_a='A',option_b='B',option_c='C',option_d='D',correct=2)
        self.client.force_login(self.student)
    def url(self,name,*args):return reverse(name,args=args or [self.course.slug])
    def enroll(self):Enrollment.objects.create(student=self.student,course=self.course)
    def finish(self):
        self.enroll();Completion.objects.create(student=self.student,lesson=self.lesson)
    def test_public_and_student_pages_render(self):
        for name in ['home','catalog','dashboard','orders','course']:
            url=reverse(name,args=[self.course.slug]) if name=='course' else reverse(name)
            self.assertEqual(self.client.get(url).status_code,200,name)
        self.client.logout()
        for url in ['/accounts/login/','/accounts/signup/']:self.assertEqual(self.client.get(url).status_code,200)
    def test_enrollment_and_completion_are_post_only_and_idempotent(self):
        self.assertEqual(self.client.get(self.url('enroll')).status_code,405)
        self.client.post(self.url('enroll'));self.client.post(self.url('enroll'))
        self.assertEqual(Enrollment.objects.count(),1)
        self.assertEqual(self.client.get(self.url('lesson',self.course.slug,self.lesson.pk)).status_code,200)
        for _ in range(2):self.client.post(self.url('complete_lesson',self.course.slug,self.lesson.pk))
        self.assertEqual(Completion.objects.count(),1)
    def test_lesson_enrollment_and_course_boundary(self):
        self.assertEqual(self.client.get(self.url('lesson',self.course.slug,self.lesson.pk)).status_code,403)
        self.enroll()
        other=Course.objects.create(title='Other',slug='other',instructor=self.owner,published=True)
        other_lesson=Lesson.objects.create(course=other,title='Private',content='secret')
        self.assertEqual(self.client.get(self.url('lesson',self.course.slug,other_lesson.pk)).status_code,404)
    def test_paid_course_cannot_be_enrolled_for_free(self):
        self.course.price=25000;self.course.save()
        self.assertRedirects(self.client.post(self.url('enroll')),self.url('checkout'))
        self.assertFalse(Enrollment.objects.exists())
    def test_quiz_requires_completion_and_server_answers(self):
        self.enroll()
        self.client.post(self.url('quiz'),{'score':100,'passed':True})
        self.assertFalse(Attempt.objects.exists())
        Completion.objects.create(student=self.student,lesson=self.lesson)
        self.client.post(self.url('quiz'),{'quiz_signature':self.course.quiz_signature(),'score':100})
        self.assertFalse(Attempt.objects.exists())
        self.client.post(self.url('quiz'),{'quiz_signature':self.course.quiz_signature(),f'q_{self.question.pk}':'1','score':100})
        self.assertFalse(Attempt.objects.get().passed)
        self.assertEqual(self.client.post(self.url('issue_certificate')).status_code,403)
    def test_certificate_requirements_snapshot_and_ownership(self):
        self.finish()
        self.assertEqual(self.client.post(self.url('issue_certificate')).status_code,403)
        self.client.post(self.url('quiz'),{'quiz_signature':self.course.quiz_signature(),f'q_{self.question.pk}':'2'})
        self.client.post(self.url('issue_certificate'));self.client.post(self.url('issue_certificate'))
        cert=Certificate.objects.get();self.assertEqual(cert.course_title,'Original course')
        self.assertEqual(self.client.get(reverse('certificate',args=[cert.pk])).status_code,200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('certificate',args=[cert.pk])).status_code,404)
    def test_changed_quiz_invalidates_old_pass(self):
        self.finish()
        old=self.course.quiz_signature()
        Attempt.objects.create(student=self.student,course=self.course,score=100,passed=True,quiz_signature=old)
        self.question.correct=3;self.question.save()
        self.assertEqual(self.client.post(self.url('issue_certificate')).status_code,403)
        self.client.post(self.url('quiz'),{'quiz_signature':old,f'q_{self.question.pk}':'2'})
        self.assertEqual(Attempt.objects.count(),1)
    def test_instructor_ownership(self):
        self.assertEqual(self.client.get(reverse('studio')).status_code,403)
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get(reverse('edit_course',args=[self.course.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('delete_content',args=[self.course.pk,'lesson',self.lesson.pk])).status_code,404)
        self.client.force_login(self.owner)
        for url in [reverse('studio'),reverse('edit_course',args=[self.course.pk]),reverse('new_content',args=[self.course.pk,'lesson']),reverse('reviews')]:
            self.assertEqual(self.client.get(url).status_code,200)
    def test_csrf_and_signup_privileges(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.student)
        self.assertEqual(client.post(self.url('enroll')).status_code,403)
        self.client.logout()
        self.client.post(reverse('signup'),{'first_name':'New','username':'new','email':'new@example.com','password1':'long-new-password-892!','password2':'long-new-password-892!','is_staff':'1','is_superuser':'1'})
        user=User.objects.get(username='new');self.assertFalse(user.is_staff or user.is_superuser)
    def test_safe_embeds(self):
        self.assertFalse(video_embed_url('https://youtube.com.attacker.test/watch?v=abcdefghijk'))
        self.assertFalse(video_embed_url('javascript:alert(1)'))
        self.assertIn('youtube-nocookie.com',video_embed_url('https://youtu.be/abcdefghijk'))
    def test_seed_does_not_overwrite(self):
        call_command('seed_demo',stdout=io.StringIO());count=Course.objects.count()
        call_command('seed_demo',stdout=io.StringIO());self.assertEqual(Course.objects.count(),count)
        self.assertFalse(PaymentMethod.objects.filter(enabled=True).exists())

class PaymentTests(TestCase):
    url = LearningTests.url
    def setUp(self):
        LearningTests.setUp(self)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.media=override_settings(MEDIA_ROOT=self.temp.name);self.media.enable();self.addCleanup(self.media.disable)
        self.method=PaymentMethod.objects.create(code='kpay',name='KPay',instructions='Merchant test instructions',enabled=True)
        self.course.price=25000;self.course.save()
    def make_order(self,**kwargs):
        defaults={'student':self.student,'course':self.course,'amount':self.course.price,'currency':'MMK','method':self.method};defaults.update(kwargs)
        return Order.objects.create(**defaults)
    def receipt_image(self):
        data=io.BytesIO();Image.new('RGB',(10,10),'white').save(data,format='PNG')
        return SimpleUploadedFile('proof.png',data.getvalue(),content_type='image/png')
    def test_manual_submission_approval_private_receipt(self):
        response=self.client.post(self.url('checkout'),{'method':'kpay','amount':'1'})
        order=Order.objects.get();self.assertEqual(order.amount,Decimal('25000'))
        url=reverse('order',args=[order.pk]);self.assertEqual(self.client.get(url).status_code,200)
        self.client.post(url,{'reference':'BANK-123','receipt':self.receipt_image()})
        order.refresh_from_db();self.assertEqual(order.status,'submitted');self.assertFalse(Enrollment.objects.exists())
        receipt=reverse('receipt',args=[order.pk]);self.assertEqual(self.client.get(receipt).status_code,200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code,404);self.assertEqual(self.client.get(receipt).status_code,403)
        review=reverse('review',args=[order.pk]);self.assertEqual(self.client.post(review,{'decision':'approve'}).status_code,403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse('reviews')).status_code,200)
        self.client.post(review,{'decision':'approve'});self.client.post(review,{'decision':'approve'})
        self.assertEqual(Enrollment.objects.count(),1);order.refresh_from_db();self.assertEqual(order.status,'paid')
    def test_disabled_method_and_card_unconfigured(self):
        self.method.enabled=False;self.method.save()
        self.assertEqual(self.client.post(self.url('checkout'),{'method':'kpay'}).status_code,404)
        self.assertEqual(self.client.post(self.url('checkout'),{'method':'card'}).status_code,400)
        self.assertFalse(Order.objects.exists())
    def test_rejection_and_invalid_upload(self):
        order=self.make_order()
        self.client.post(reverse('order',args=[order.pk]),{'reference':'123','receipt':SimpleUploadedFile('fake.png',b'<script>bad</script>')})
        order.refresh_from_db();self.assertEqual(order.status,'pending')
        order.status='submitted';order.save();self.client.force_login(self.owner)
        self.client.post(reverse('review',args=[order.pk]),{'decision':'reject','note':'Transfer not found'})
        order.refresh_from_db();self.assertEqual(order.status,'rejected');self.assertFalse(Enrollment.objects.exists())
    @override_settings(STRIPE_SECRET_KEY='sk_test_example',STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_signed_webhook_exact_match_and_idempotency(self):
        order=self.make_order(method=None,amount='20.00',currency='USD',stripe_session='cs_test_123')
        event={'id':'evt_123','type':'checkout.session.completed','livemode':False,'data':{'object':{'id':'cs_test_123','client_reference_id':str(order.pk),'mode':'payment','payment_status':'paid','amount_total':2000,'currency':'usd'}}}
        def send(payload,secret='whsec_test'):
            body=json.dumps(payload);stamp=str(int(time.time()));sig=hmac.new(secret.encode(),f'{stamp}.{body}'.encode(),hashlib.sha256).hexdigest()
            return self.client.post(reverse('stripe_webhook'),body,content_type='application/json',HTTP_STRIPE_SIGNATURE=f't={stamp},v1={sig}')
        self.assertEqual(send(event,'wrong').status_code,400)
        event['data']['object']['amount_total']=1;self.assertEqual(send(event).status_code,400)
        self.assertFalse(Enrollment.objects.exists())
        event['data']['object']['amount_total']=2000
        self.assertEqual(send(event).status_code,200);self.assertEqual(send(event).status_code,200)
        self.assertEqual(Enrollment.objects.count(),1)
    @override_settings(STRIPE_SECRET_KEY='sk_test_example',STRIPE_WEBHOOK_SECRET='whsec_test')
    @patch('learning.payments.stripe.checkout.Session.create')
    def test_checkout_uses_server_price_and_return_url_does_not_fulfill(self,create):
        self.course.currency='USD';self.course.price=20;self.course.save()
        create.return_value.id='cs_test_new';create.return_value.url='https://checkout.stripe.com/example'
        self.assertEqual(self.client.post(self.url('checkout'),{'method':'card','amount':'1'}).status_code,302)
        self.assertEqual(create.call_args.kwargs['line_items'][0]['price_data']['unit_amount'],2000)
        order=Order.objects.get();self.client.get(reverse('order',args=[order.pk])+'?paid=true')
        self.assertFalse(Enrollment.objects.exists())

    def test_merchant_qr_type_and_restricted_admin(self):
        self.method.qr=self.receipt_image();self.method.save()
        response=self.client.get(reverse('merchant_qr',args=[self.method.pk]))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response['Content-Type'],'image/png')
        response.close()
        self.client.force_login(self.teacher)
        self.assertEqual(self.client.get('/admin/learning/paymentmethod/').status_code,403)
        self.assertEqual(self.client.get(reverse('reviews')).status_code,403)
