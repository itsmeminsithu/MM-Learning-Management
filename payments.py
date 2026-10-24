"""Private manual receipts and signed hosted-card fulfillment.
Copyright (c) 2026 Min SiThu (devminsithu). SPDX-License-Identifier: MIT
"""
import uuid
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Course, Enrollment, Order, PaymentMethod
from .forms import ReceiptForm


def cards_enabled(course):
    return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET and course.currency in ('USD','THB'))

@login_required
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug, published=True)
    if Enrollment.objects.filter(student=request.user, course=course).exists() or course.price <= 0:
        return redirect('course', slug=slug)
    if not course.lessons.exists(): raise PermissionDenied('Course is not ready.')
    methods = PaymentMethod.objects.filter(enabled=True, currency=course.currency)
    if request.method == 'POST':
        selected = request.POST.get('method', '')
        if selected == 'card':
            if not cards_enabled(course): return HttpResponseBadRequest('Cards are not configured for this currency.')
            order = Order.objects.create(student=request.user, course=course, amount=course.price, currency=course.currency)
            try:
                session = stripe.checkout.Session.create(
                    api_key=settings.STRIPE_SECRET_KEY, mode='payment', payment_method_types=['card'],
                    client_reference_id=str(order.id),
                    line_items=[{'price_data': {'currency':course.currency.lower(), 'unit_amount':int(course.price*100),
                       'product_data':{'name':course.title}}, 'quantity':1}],
                    success_url=request.build_absolute_uri(reverse('order',args=[order.id])),
                    cancel_url=request.build_absolute_uri(reverse('order',args=[order.id])),
                    idempotency_key=str(order.id))
                order.stripe_session = session.id
                order.save(update_fields=['stripe_session'])
                return redirect(session.url)
            except stripe.StripeError:
                order.status='rejected';order.review_note='Checkout could not be started. No enrollment granted.'
                order.save(update_fields=['status','review_note'])
                messages.error(request,'Card checkout is unavailable. Contact the academy or try again later.')
        else:
            method = get_object_or_404(methods, code=selected)
            order = Order.objects.create(student=request.user, course=course, amount=course.price, currency=course.currency, method=method)
            return redirect('order', pk=order.id)
    return render(request,'learning/checkout.html',{'course':course,'methods':methods,'cards_enabled':cards_enabled(course)})

@login_required
def orders(request):
    return render(request,'learning/orders.html',{'orders':Order.objects.filter(student=request.user).select_related('course','method')})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, student=request.user)
    form = ReceiptForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if not order.method_id or order.status != 'pending': return HttpResponseBadRequest('This order cannot accept a receipt.')
        if form.is_valid():
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=pk)
                if locked.status != 'pending': return HttpResponseBadRequest('Order already submitted.')
                locked.reference = form.cleaned_data['reference'];locked.receipt = form.cleaned_data['receipt']
                locked.status='submitted';locked.save(update_fields=['reference','receipt','status'])
            messages.success(request,'Receipt submitted. Course access opens after payment is verified.')
            return redirect('order',pk=pk)
    return render(request,'learning/order.html',{'order':order,'form':form})

@login_required
def receipt(request,pk):
    order = get_object_or_404(Order,pk=pk)
    if request.user != order.student and not request.user.is_superuser: raise PermissionDenied
    if not order.receipt: return HttpResponse(status=404)
    response=FileResponse(order.receipt.open('rb'),as_attachment=True,filename='payment-receipt',content_type='application/octet-stream')
    response['Cache-Control']='private, no-store'
    return response

@login_required
def merchant_qr(request,pk):
    method=get_object_or_404(PaymentMethod,pk=pk,enabled=True)
    if not method.qr:return HttpResponse(status=404)
    from PIL import Image
    stream=method.qr.open('rb')
    try:
        image_format=Image.open(stream).format
        stream.seek(0)
    except (OSError, ValueError):
        stream.close()
        return HttpResponse(status=404)
    response=FileResponse(stream, content_type=Image.MIME.get(image_format, 'application/octet-stream'))
    response['Cache-Control']='private, no-store'
    return response

@login_required
def reviews(request):
    if not request.user.is_superuser: raise PermissionDenied
    return render(request,'learning/reviews.html',{'orders':Order.objects.filter(status='submitted').select_related('course','student','method')})

@login_required
@require_POST
def review(request,pk):
    if not request.user.is_superuser: raise PermissionDenied
    decision=request.POST.get('decision')
    if decision not in ('approve','reject'):return HttpResponseBadRequest('Invalid decision')
    with transaction.atomic():
        order=get_object_or_404(Order.objects.select_for_update(),pk=pk)
        if order.status != 'submitted' or not order.method_id: return HttpResponseBadRequest('Order is not awaiting manual review.')
        order.reviewed_by=request.user;order.review_note=request.POST.get('note','')[:500]
        order.status='paid' if decision=='approve' else 'rejected'
        if decision=='approve':
            order.paid_at=timezone.now()
            Enrollment.objects.get_or_create(student=order.student,course=order.course)
        order.save()
    messages.success(request,'Payment review recorded.')
    return redirect('reviews')

@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET: return HttpResponse(status=503)
    try:
        event=stripe.Webhook.construct_event(request.body,request.headers.get('Stripe-Signature',''),settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError,stripe.SignatureVerificationError): return HttpResponseBadRequest('Invalid signature')
    if event['type'] not in ('checkout.session.completed','checkout.session.async_payment_succeeded'):
        return HttpResponse(status=200)
    session=event['data']['object']
    if session.get('payment_status') != 'paid':return HttpResponse(status=200)
    try: pk=uuid.UUID(session.get('client_reference_id',''))
    except (ValueError,TypeError,AttributeError):return HttpResponseBadRequest('Invalid order')
    with transaction.atomic():
        order=Order.objects.select_for_update().filter(pk=pk,method__isnull=True).first()
        # A retry will handle the rare race where the event precedes saving session.id.
        if not order or not order.stripe_session:return HttpResponse(status=409)
        if (session.get('id') != order.stripe_session or session.get('currency') != order.currency.lower()
            or session.get('amount_total') != int(order.amount*100) or session.get('mode') != 'payment'
            or bool(event.get('livemode')) != settings.STRIPE_SECRET_KEY.startswith('sk_live_')):
            return HttpResponseBadRequest('Payment mismatch')
        if order.status == 'paid':return HttpResponse(status=200)
        if order.status != 'pending':return HttpResponseBadRequest('Order cannot be fulfilled')
        order.status='paid';order.paid_at=timezone.now();order.save(update_fields=['status','paid_at'])
        Enrollment.objects.get_or_create(student=order.student,course=order.course)
    return HttpResponse(status=200)
