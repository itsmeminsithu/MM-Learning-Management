# Copyright (c) 2026 Min SiThu (devminsithu). SPDX-License-Identifier: MIT
from .models import Completion, Attempt, Certificate

def course_progress(user,course):
    lessons = list(course.lessons.all())
    done = set(Completion.objects.filter(student=user,lesson__course=course).values_list('lesson_id',flat=True))
    total = len(lessons)
    complete = sum(lesson.id in done for lesson in lessons)
    next_lesson = next((lesson for lesson in lessons if lesson.id not in done),lessons[0] if lessons else None)
    has_quiz = course.questions.exists()
    passed = Attempt.objects.filter(student=user,course=course,quiz_signature=course.quiz_signature(),passed=True).exists() if has_quiz else True
    return {'done':done,'total':total,'complete':complete,'percent':round(complete*100/total) if total else 0,
            'next_lesson':next_lesson,'has_quiz':has_quiz,'passed':passed,
            'eligible':total>0 and complete==total and passed,
            'certificate':Certificate.objects.filter(student=user,course=course).first()}
