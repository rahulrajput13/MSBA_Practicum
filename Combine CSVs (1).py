#!/usr/bin/env python
# coding: utf-8

# In[33]:


from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
database = client['Practicum']
collection = database['AMD_Laptops']
#rank = element['Details']['rank']
query = collection.find({},{"Reviews.Overview":1}).limit(10)
for q in query:
    #print(q)
    print()
    print(q["Reviews"][0]['Overview']) # Convert to json object to use as dict from json.loads


# In[27]:


query2 = collection.find({},{"Reviews.All_Reviews":1}).limit(10)
for q2 in query2:
    #print(q2)
    print()
    print(q2["Reviews"][0]["All_Reviews"])

