#!/usr/bin/env python
# coding: utf-8

# If you face the following error: 'IndexError: single positional indexer is out-of-bounds', try skipping the particular laptop number at which the error came by manually changing the value of i to the next one in the for loop in Section 2. 

# In[ ]:


from bs4 import BeautifulSoup
import requests
import re
import time
import pandas as pd
import random
import os
import csv
from pymongo import MongoClient
from json import dumps

def main():

############################## SECTION 1 ########################################################################
#### Loading files from Local and parse into BeautifulSoup objects - CHANGE DIRECTORY accordingly
    directory = '/Users/rahulrajput/Desktop/MSBA/Winter/462 - Practicum/AMD Laptops'
    output_text = ""
    cnt = 1
    final_laptop_outputs = {}
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)

        with open(path, "rb") as file:
            final_laptop_soup = BeautifulSoup(file)

        final_laptop_outputs["Laptop_" + str(cnt)] = final_laptop_soup
        print(cnt)
        cnt = cnt + 1

############################## SECTION 2 ########################################################################
#### Storing each Laptop Data into a Master Dictionary    
    AMD_Laptops = [] # Master dictionary for Qualcomm

    client = MongoClient('mongodb://localhost:27017/')
    database = client['Practicum']
    collection = database['AMD_Laptops']    

    to_store = ['Title','Pricing','Features_Overview','About_Item','Suggested_Laptops','QnA','Reviews']
    Laptop_AMD_Info = dict.fromkeys(to_store) # Dictionary to store data from each laptop

    for i in range(0,len(final_laptop_outputs)+1):

        # Selecting Title
        Laptop_AMD_Info['Title'] = get_title(final_laptop_outputs["Laptop_" + str(i)])
        #print(Laptop_Qualcomm_Info['Title'])

        # Selecting Prices
        Laptop_AMD_Info['Pricing'] = get_price(final_laptop_outputs["Laptop_" + str(i)])
        #print(Laptop_Qualcomm_Info['Pricing'])

        # Selecting Features Overview Text
        Laptop_AMD_Info['Features_Overview'] = get_features_overview(final_laptop_outputs["Laptop_" + str(i)])    
        #print(Laptop_Qualcomm_Info['Features_Overview'])

        # Selecting About Item Text
        Laptop_AMD_Info['About_Item'] = get_about_item(final_laptop_outputs["Laptop_" + str(i)])
        #print(Laptop_Qualcomm_Info['About_Item'])

        # Selecting text from Suggested Items
        Laptop_AMD_Info['Suggested_Laptops'] = get_comparisons(final_laptop_outputs["Laptop_" + str(i)])        
        #print(Laptop_Qualcomm_Info['Suggested_Laptops'])

        # Selecting Reviews text
        first_url = get_first_reviews_url(final_laptop_outputs["Laptop_" + str(i)])

        review_page_soups = []
        test = get_all_review_soups(first_url, review_page_soups)                               

        All_Reviews = []
        for soup in review_page_soups:
            all_types_reviews = dict.fromkeys(['Overview','Top_Reviews','All_Reviews'])
            
            all_types_reviews['Overview'] = get_reviews_table(soup)
            all_types_reviews['Top_Reviews'] = get_top_reviews(soup)
            all_types_reviews['All_Reviews'] = get_reviews(soup)
            
            All_Reviews.append(all_types_reviews)

        Laptop_AMD_Info['Reviews'] = All_Reviews

        # Selecting QnA text
        first_url_qna = get_first_qna_url(final_laptop_outputs["Laptop_" + str(i)])

        qna_soups = []
        soups_qna = get_all_qnas_soups(first_url_qna,qna_soups)

        All_Questions = []
        if soups_qna is not None:
            for soup in soups_qna:
                All_Questions.append(get_questions(soup))
        else:
            pass

        Laptop_AMD_Info['QnA'] = All_Questions

        
        # Storing each laptop data
        print(Laptop_AMD_Info)
        AMD_Laptops.append(Laptop_AMD_Info)
        
        doc = {
            "Title": Laptop_AMD_Info["Title"],
             "Pricing": Laptop_AMD_Info["Pricing"],
             "Features_Overview": Laptop_AMD_Info["Features_Overview"],
             "About_Item": Laptop_AMD_Info["About_Item"],
             "Suggested_Laptops": Laptop_AMD_Info["Suggested_Laptops"],
             "QnA": Laptop_AMD_Info["QnA"],
             "Reviews": Laptop_AMD_Info["Reviews"]}
       
        collection.insert_one(doc)
        
        with open(f'AMD_Data_{i}.csv', mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=to_store)
            writer.writeheader()
            writer.writerow(Laptop_AMD_Info)       

############################## SECTION 3 ########################################################################
#### Creating functions to extract information from Laptop Pages    
    
def get_title(soup_input):
    if soup_input.select('span#productTitle'):
        title_string = re.search('\s*([a-zA-Z0-9].+)\s*',soup_input.select('span#productTitle')[0].text)
        title = title_string.group(1)
        return title
    else:
        return None    


def get_price(soup_input):
    if soup_input.select('div#apex_desktop'):
        for i in soup_input.select('div#apex_desktop'):
            prices = re.findall('\s*([0-9.]+)',i.text.strip())
            return prices
    else:
        return None
    
    
def get_features_overview(soup_input):
    if soup_input.select('div#productOverview_feature_div table.a-normal.a-spacing-micro'):
        
        features_table = soup_input.select('div#productOverview_feature_div table.a-normal.a-spacing-micro')
        features_df = pd.read_html(str(features_table))[0]
        
        dict_FO = features_df.to_dict()
        new_dict_FO_keys = features_df.iloc[:,0]
        new_dict_FO_values = features_df.iloc[:,1]
        new_dict_FO = dumps(dict(zip(new_dict_FO_keys,new_dict_FO_values)))        
        
        return new_dict_FO
    else:
        return None
    
    
def get_about_item(soup_input):
    if soup_input.find('div',{'id':'feature-bullets'}):
        details = soup_input.find('div',{'id':'feature-bullets'})
        About = []
        for li in details.find_all('li'):
            About.append(li.text.strip())
        return About
    else:
        return None
    

def get_comparisons(soup_input, SI_output = None):
     if soup_input.find("table",{"id":"HLCXComparisonTable"}):
        if SI_output is None:
            SI_output = []        
        
        tbl = soup_input.find("table",{"id":"HLCXComparisonTable"})
        data_frame = pd.read_html(str(tbl))[0]
        data_frame2 = data_frame.drop(labels=[1,2], axis=0).reset_index(drop=True)
        
        new_dict_SI_keys = data_frame2.iloc[:,0]
        new_dict_SI_keys[0,0] = 'Name'
        
        for col in data_frame2.iloc[:, 1:]:
            new_dict_SI_values = data_frame2.iloc[:,col]
            new_dict_SI = dumps(dict(zip(new_dict_SI_keys,new_dict_SI_values)))            
            SI_output.append(new_dict_SI)
        
        return SI_output
     else:
        return None
    
###### Reviews Section #######
def get_first_reviews_url(soup_input):    
    output_url = None
    
    if soup_input.find("table",{"id":"productDetails_detailBullets_sections1"}):
        table = soup_input.find("table",{"id":"productDetails_detailBullets_sections1"})
        data_frame = pd.read_html(str(table))[0]
        asin = data_frame[data_frame.iloc[:,0] == 'ASIN']
        final_asin = asin.iloc[0,1]
        if final_asin is not None:
            output_url = "https://www.amazon.com/product-reviews/" + final_asin
            return output_url
        else:
            return None
    else:
        return None
    
def get_all_review_soups(given_url,All_Review_Soups = None):   
    
    if given_url is not None:
        if All_Review_Soups is None:
            All_Review_Soups = []        

        headers = {
                'authority': 'fls-na.amazon.com',
                'pragma': 'no-cache',
                'method': 'GET',
                'cache-control': 'no-cache',
                'dnt': '1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-dest': 'document',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'
        }    

        session_reviews = requests.Session()
        reviews_page = session_reviews.get(given_url, headers=headers)
        print("The status code for website access is :",reviews_page.status_code)
        ######## STORE LAPTOP REVIEWS LOCALLY ############
        with open(f"AMDReviews_{random.randint(0,10000)}.htm", "w", encoding="utf-8") as file:
            file.write(reviews_page.text)
        
        review_soup = BeautifulSoup(reviews_page.text, 'html.parser')
        #print(review_soup)

        All_Review_Soups.append(review_soup)
        #print(len(All_Review_Soups))

        pagination_link = review_soup.select_one('ul.a-pagination li.a-last a')

        if pagination_link is None or len(All_Review_Soups) == 15:
            print('done')
            return All_Review_Soups    

        next_url = "https://www.amazon.com/" + pagination_link['href']
        print(next_url)

        if next_url == given_url:
            return All_Review_Soups

        time.sleep(3)
        return get_all_review_soups(next_url, All_Review_Soups)
    else:
        return None
    
def get_reviews(review_soup): # Getting all reviews
    
    if review_soup is not None: # Checking whether there is atleast on review
        try:
            all_reviews = [] # List to store all reviews present on particular page
            
            # Narrowing down the page element under which reviews are present
            for k in review_soup.select('div.a-section.review.aok-relative'):
                all_reviews.append(k.text.strip())

        except AttributeError:
            print('No reviews')

        return all_reviews    
    else:
        return None
    
def get_reviews_table(review_soup): # Getting the star ratings
    
    if review_soup is not None: # Checking whether there is atleast one rating
        
        # Identifying the tabular element which stores the ratings
        if bool(review_soup.find("table",{"id":"histogramTable"})) is True:
            reviews_table = review_soup.find("table",{"id":"histogramTable"})
            
            # Using pandas to directly store the reviews table as a Dataframe object
            data_frame_reviews = pd.read_html(str(reviews_table))[0]

            new_dict_RT_keys = ['5 Star','4 Star','3 Star','2 Star','1 Star']
            new_dict_RT_values = data_frame_reviews.iloc[:,2]
            # Converting the ratings table as a dictionary for storage.
            new_dict_RT = dumps(dict(zip(new_dict_RT_keys,new_dict_RT_values)))   

            return new_dict_RT
        else:
            return None
    else:
        return None
    
def get_top_reviews(review_soup):
    if review_soup is not None:
        if bool(review_soup.select("div#cm_cr-rvw_summary")) is True:
            try:        
                top_reviews = []
                for j in review_soup.select("div#cm_cr-rvw_summary"):
                    top_reviews.append(j.text.strip())

            except AttributeError:
                print('No top reviews')
            
            return top_reviews
        else:
            return None
    else:
        return None

###################################################################################################### 

##### QNA Section #####

def get_first_qna_url(soup_input):
    
    if soup_input.select('div.a-section.cdQuestionAnswerBucket a.a-link-emphasis'):
        for i in soup_input.select('div.a-section.cdQuestionAnswerBucket a.a-link-emphasis'):
            qa_url = "https://www.amazon.com" + i['href']

        return qa_url
    else:
        return None

All_QNA_Soups = []
def get_all_qnas_soups(qa_url,All_QNA_Soups = None):
        
    if qa_url is not None:
        if All_QNA_Soups is None:
            All_QNA_Soups = []

        headers = {
            'authority': 'fls-na.amazon.com',
            'pragma': 'no-cache',
            'method': 'POST',
            'cache-control': 'no-cache',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

        session_qna = requests.Session()
        qna_page = session_qna.get(qa_url, headers=headers)
        print("The status code for website access is :",qna_page.status_code)
        ######## STORE LAPTOP REVIEWS LOCALLY ############
        with open(f"AMDQNA_{random.randint(0,10000)}.htm", "w", encoding="utf-8") as file:
            file.write(qna_page.text)        
        qna_soup = BeautifulSoup(qna_page.text, 'html.parser')

        All_QNA_Soups.append(qna_soup)

        pagination_link = qna_soup.select_one('ul.a-pagination li.a-last a')       

        if pagination_link is None or len(All_QNA_Soups) == 10:
            print('done')
            return All_QNA_Soups         

        next_url = "https://www.amazon.com/" + pagination_link['href']
        print(next_url)

        if next_url == qa_url:
            return All_QNA_Soups

        time.sleep(3)
        return get_all_qnas_soups(next_url, All_QNA_Soups)
    else:
        return None

def get_questions(qna_soup):
    
    if qna_soup is not None:
        Questions = []

        questions = qna_soup.select('div.a-section.askTeaserQuestions span.a-declarative')
        for q in questions:
            Questions.append(q.text.strip())

        return Questions
    else:
        return None

###################################################################################################### 
    
if __name__ == "__main__":
    main()


# In[ ]:




