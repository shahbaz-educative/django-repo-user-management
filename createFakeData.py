ccimport os 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "helloworld.settings")

import django 
django.setup() 

from faker import factory,Faker 
from sample_app.models import * 
from model_bakery.recipe import Recipe,foreign_key 

fake = Faker() 

for k in range(100):
    author=Recipe(Author,
                name=fake.name(),
                createdDate=fake.future_datetime(end_date="+30d", tzinfo=None),
                updatedDate=fake.future_datetime(end_date="+30d", tzinfo=None),)
  
    question=Recipe(Question, 
                question_text=fake.sentence(nb_words=6,variable_nb_words=True),
                pub_date=fake.future_datetime(end_date="+30d",tzinfo=None),
                refAuthor=foreign_key(author),
                createdDate=fake.future_datetime(end_date="+30d",tzinfo=None),
                updatedDate=fake.future_datetime(end_date="+30d",tzinfo=None),)
    
    choice = Recipe(Choice, 
                question=foreign_key(question), 
                choice_text = fake.sentence(nb_words=1, variable_nb_words=True), 
                createdDate=fake.future_datetime(end_date="+30d", tzinfo=None),  
                updatedDate=fake.future_datetime(end_date="+30d", tzinfo=None), ) 
    choice.make()
