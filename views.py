"""Server-side authorization, enrollment and assessment.
Copyright (c) 2026 Min SiThu (devminsithu). SPDX-License-Identifier: MIT
"""
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Course, Lesson, Question, Enrollment, Completion, Attempt, Certificate
from .forms import SignupForm, CourseForm, LessonForm, QuestionForm
from .services import course_progress


def home(request):
    courses = Course.objects.filter(published=True).select_related('instructor').annotate(lesson_count=Count('lessons'))[:3]
    return render(request,'learning/home.html',{'courses':courses})


def catalog(request):
    courses = Course.objects.filter(published=True).select_related('instructor').annotate(lesson_count=Count('lessons'))
    categories = list(courses.order_by('category').values_list('category',flat=True).distinct())
    query = request.GET.get('q','').strip()[:100]
    category = request.GET.get('category','')
    if query: courses = courses.filter(Q(title__icontains=query)|Q(summary__icontains=query))
    if category: courses = courses.filter(category=category)
    return render(request,'learning/catalog.html',{'courses':courses,'categories':categories,'query':query,'selected_category':category})


def signup(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form = SignupForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save()
        login(request,user)
        messages.success(request,'Your learning journey starts here. Welcome!')
        return redirect('dashboard')
    return render(request,'registration/signup.html',{'form':form})


def course_detail(request,slug):
    course = get_object_or_404(Course,published=True,slug=slug)
    enrolled = request.user.is_authenticated and Enrollment.objects.filter(student=request.user,course=course).exists()
    progress = course_progress(request.user,course) if enrolled else None
    return render(request,'learning/course.html',{'course':course,'enrolled':enrolled,'progress':progress})


@login_required
@require_POST
def enroll(request,slug):
    course = get_object_or_404(Course,published=True,slug=slug)
    if not course.lessons.exists():
        messages.error(request,'This course is not ready for enrollment yet.')
        return redirect('course',slug=slug)
    if course.price > 0:
        return redirect('checkout',slug=slug)
    Enrollment.objects.get_or_create(student=request.user,course=course)
    messages.success(request,'You are enrolled. Let’s get started.')
    return redirect('course',slug=slug)


@login_required
def dashboard(request):
    enrollments=Enrollment.objects.filter(student=request.user).select_related('course')
    rows=[{'course':e.course,'progress':course_progress(request.user,e.course)} for e in enrollments]
    return render(request,'learning/dashboard.html',{'rows':rows,'certificates':Certificate.objects.filter(student=request.user),
        'completed_count':sum(r['progress']['eligible'] for r in rows)})


def enrolled_course(request,slug):
    course=get_object_or_404(Course,published=True,slug=slug)
    if not Enrollment.objects.filter(student=request.user,course=course).exists():
        raise PermissionDenied('Enroll in this course before accessing lessons.')
    return course


@login_required
def lesson(request,slug,pk):
    course=enrolled_course(request,slug)
    item=get_object_or_404(Lesson,course=course,pk=pk)
    return render(request,'learning/lesson.html',{'course':course,'lesson':item,'progress':course_progress(request.user,course)})


@login_required
@require_POST
def complete_lesson(request,slug,pk):
    course=enrolled_course(request,slug)
    item=get_object_or_404(Lesson,course=course,pk=pk)
    Completion.objects.get_or_create(student=request.user,lesson=item)
    progress=course_progress(request.user,course)
    if progress['complete']==progress['total']:
        messages.success(request,'All lessons complete. Take the quiz to finish.' if progress['has_quiz'] else 'All lessons complete. Your certificate is ready.')
        return redirect('quiz' if progress['has_quiz'] else 'course',slug=slug)
    return redirect('lesson',slug=slug,pk=progress['next_lesson'].pk)


@login_required
def quiz(request,slug):
    course=enrolled_course(request,slug)
    progress=course_progress(request.user,course)
    questions=list(course.questions.all())
    result=None
    if not progress['total'] or progress['complete']!=progress['total']:
        messages.error(request,'Complete every lesson before taking the quiz.')
        return redirect('course',slug=slug)
    if not questions:
        return redirect('course',slug=slug)
    if request.method=='POST':
        signature=course.quiz_signature()
        if request.POST.get('quiz_signature')!=signature:
            messages.error(request,'The quiz has changed. Please answer the current questions.')
            return redirect('quiz',slug=slug)
        answers=[request.POST.get(f'q_{q.pk}') for q in questions]
        if any(a not in ('1','2','3','4') for a in answers):
            messages.error(request,'Answer every question before submitting.')
        else:
            correct=sum(int(answer)==q.correct for answer,q in zip(answers,questions))
            score=correct*100//len(questions)
            result=Attempt.objects.create(student=request.user,course=course,score=score,
                passed=correct*100>=course.pass_percentage*len(questions),quiz_signature=signature)
            progress=course_progress(request.user,course)
    return render(request,'learning/quiz.html',{'course':course,'questions':questions,'progress':progress,
        'result':result,'quiz_signature':course.quiz_signature(),
        'attempts':Attempt.objects.filter(student=request.user,course=course)[:5]})


@login_required
@require_POST
def issue_certificate(request,slug):
    course=enrolled_course(request,slug)
    existing=Certificate.objects.filter(student=request.user,course=course).first()
    if existing: return redirect('certificate',pk=existing.pk)
    if not course_progress(request.user,course)['eligible']:
        raise PermissionDenied('Complete the course and pass its quiz to earn a certificate.')
    cert,_=Certificate.objects.get_or_create(student=request.user,course=course,defaults={
        'student_name':request.user.get_full_name() or request.user.username,'course_title':course.title})
    return redirect('certificate',pk=cert.pk)


@login_required
def certificate(request,pk):
    cert=get_object_or_404(Certificate,pk=pk,student=request.user)
    return render(request,'learning/certificate.html',{'certificate':cert})


def instructor_required(view):
    @login_required
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        if not request.user.is_staff: raise PermissionDenied('Instructor access is required.')
        return view(request,*args,**kwargs)
    return wrapped


def owned_course(user,pk):
    courses=Course.objects.all() if user.is_superuser else Course.objects.filter(instructor=user)
    return get_object_or_404(courses,pk=pk)


@instructor_required
def studio(request):
    courses=Course.objects.all() if request.user.is_superuser else Course.objects.filter(instructor=request.user)
    return render(request,'learning/studio.html',{'courses':courses.annotate(learner_count=Count('enrollments',distinct=True),lesson_count=Count('lessons',distinct=True))})


@instructor_required
def edit_course(request,pk=None):
    course=owned_course(request.user,pk) if pk else None
    form=CourseForm(request.POST or None,instance=course)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False)
        if not course:item.instructor=request.user
        item.save()
        messages.success(request,'Course saved.')
        return redirect('edit_course',pk=item.pk)
    return render(request,'learning/edit_course.html',{'form':form,'course':course})


@instructor_required
def edit_content(request,course_pk,kind,pk=None):
    course=owned_course(request.user,course_pk)
    if kind not in ('lesson','question'):return HttpResponseBadRequest('Unknown content type')
    model,form_class=(Lesson,LessonForm) if kind=='lesson' else (Question,QuestionForm)
    instance=get_object_or_404(model,course=course,pk=pk) if pk else None
    form=form_class(request.POST or None,instance=instance)
    if request.method=='POST' and form.is_valid():
        item=form.save(commit=False);item.course=course;item.save()
        messages.success(request,f'{kind.title()} saved.')
        return redirect('edit_course',pk=course.pk)
    return render(request,'learning/edit_content.html',{'form':form,'course':course,'kind':kind,'item':instance})


@instructor_required
@require_POST
def delete_content(request,course_pk,kind,pk):
    course=owned_course(request.user,course_pk)
    if kind not in ('lesson','question'):return HttpResponseBadRequest('Unknown content type')
    model=Lesson if kind=='lesson' else Question
    get_object_or_404(model,course=course,pk=pk).delete()
    messages.success(request,f'{kind.title()} deleted.')
    return redirect('edit_course',pk=course.pk)
