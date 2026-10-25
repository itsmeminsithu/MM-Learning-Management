from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from learning.models import Course, Lesson, Question, PaymentMethod

class Command(BaseCommand):
    help = 'Add original sample lessons and disabled payment methods without replacing existing content.'
    def handle(self, *args, **kwargs):
        author, created = User.objects.get_or_create(username='sample_author', defaults={'first_name':'MM Learning','is_active':False})
        if created: author.set_unusable_password();author.save()
        samples = [
          ('digital-foundations','Digital foundations for everyday work','Technology','teal',0,
           'Build a calmer, more confident digital workflow.',
           [('Make a home for your files','A clear file structure helps you find work later. Create a folder for each project and keep source material separate from finished exports.\n\nUse descriptive names such as lesson-plan-2026-10 rather than final-final-new. Keep one authoritative copy and archive older versions.\n\nPractice: create a project folder with Notes, Source and Exports subfolders. Write a short naming rule you can reuse.'),
            ('Protect your accounts','Use a unique password for each account and store it in a password manager. Enable multi-factor authentication where available.\n\nCheck the destination of a link before signing in. If a message creates urgency, open the service through a known address instead. Keep recovery codes somewhere safe.\n\nPractice: review the recovery options for one account. Never put real passwords into your course notes.')],
           ('Which approach makes files easier to find?','Descriptive names and a consistent folder structure','Renaming every file final','Keeping all files on the desktop','Deleting all previous work')),
          ('design-with-purpose','Design with purpose','Design','coral',0,
           'Turn a messy idea into a clear, useful screen.',
           [('Start with one task','Before drawing a screen, write the main task a person needs to complete. A course page might help someone decide whether the course fits their goals.\n\nList the information needed for that decision: outcomes, level, curriculum and price. Remove decoration that competes with these details.\n\nPractice: sketch a course page using only a title, description, curriculum and one primary action.'),
            ('Make the next action clear','Hierarchy gives important information more attention. Use spacing, size and clear labels to guide the reader.\n\nKeep text readable, provide visible keyboard focus, and do not communicate status through color alone. Label form fields directly.\n\nPractice: replace an unclear button label such as Go with a specific action such as Start lesson.')],
           ('What should guide a screen design?','The task the person needs to complete','The maximum number of colors','Every available animation','The largest possible logo')),
          ('plan-your-first-project','Plan your first independent project','Business','blue',25000,
           'Define a small outcome and make a realistic delivery plan.',
           [('Define a useful outcome','Describe the problem, the person affected and one useful result. A small project becomes manageable when you can explain what done means.\n\nWrite three acceptance criteria. For a study planner, these might be adding a task, choosing a date and marking a task complete.\n\nPractice: write one sentence describing your project and three checks that would demonstrate success.'),
            ('Plan for feedback','Break the project into small milestones. Build a version someone can try before polishing every detail. Ask them to complete a real task and observe where they hesitate.\n\nKeep a list of changes and choose the next improvement based on evidence. Reserve time for documentation and maintenance.\n\nPractice: schedule one feedback session and write three questions that focus on how the product is used.')],
           ('When is feedback most useful?','While there is still time to improve the project','Only after every decision is permanent','Never','Only when it is praise')),
        ]
        for slug,title,category,accent,price,summary,lessons,quiz in samples:
            course, created = Course.objects.get_or_create(slug=slug,defaults={'title':title,'category':category,'accent':accent,'price':price,'summary':summary,'description':summary+' This short sample course demonstrates the learning workflow. Replace or extend it with your own teaching material.','instructor':author,'published':True})
            if created:
                for index,(name,content) in enumerate(lessons,1):Lesson.objects.create(course=course,title=name,content=content,position=index)
                Question.objects.create(course=course,prompt=quiz[0],option_a=quiz[1],option_b=quiz[2],option_c=quiz[3],option_d=quiz[4],correct=1)
        for code,name in [('kpay','KPay (KBZPay)'),('wavepay','WavePay'),('aya','AYA Bank'),('kbz','KBZ Bank'),('mmqr','MMQR')]:
            PaymentMethod.objects.get_or_create(code=code,defaults={'name':name,'instructions':'','enabled':False})
        self.stdout.write(self.style.SUCCESS('Sample content ready. Payment methods remain disabled until configured.'))
