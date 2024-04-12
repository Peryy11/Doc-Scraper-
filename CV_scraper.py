from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
import spacy
from spacy.matcher import Matcher
import re 
#from transformers import AutoTokenizer, AutoModelForTokenClassification
#from transformers import pipeline
import pandas as pd
#replace with proper path
file_path = r"path/to/pdf"
text = ''

def remove_unicode(text):
    cleaned_text = text.encode('ascii', 'ignore').decode('ascii')
    return cleaned_text

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as fh:
        # iterate over all pages of PDF document
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            # creating a resource manager
            resource_manager = PDFResourceManager()
            
            # create a file handle
            fake_file_handle = io.StringIO()
            
            # creating a text converter object
            converter = TextConverter(
                                resource_manager, 
                                fake_file_handle, 
                                codec='utf-8', 
                                laparams=LAParams()
                        )

            # creating a page interpreter
            page_interpreter = PDFPageInterpreter(
                                resource_manager, 
                                converter
                            )

            # process current page
            page_interpreter.process_page(page)

            # extract text
            text = fake_file_handle.getvalue()

            # Remove special characters
            text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
            text = text.replace('','')
            
            # extract text
            text = fake_file_handle.getvalue()
            text = re.sub(r'\n+', '\n', text)  # Remove consecutive line breaks
            text = re.sub(r'\n\s+', ' ', text)  # Remove leading spaces after line breaks

            # Remove Unicode characters
            text = remove_unicode(text)

            yield text

            # close open handles
            converter.close()
            fake_file_handle.close()

# calling above function and extracting text
cleaned_text = ''
for page in extract_text_from_pdf(file_path):
    cleaned_text += ' ' + page

#print(cleaned_text)

#extracting the 1st 5% of the text
def extract_first_percentage(text, percentage):
    total_characters = len(text)
    percentage_characters = int(total_characters * (percentage / 100))
    return text[:percentage_characters]

# Example usage:
first_5_percent = extract_first_percentage(cleaned_text, 5)
#print(first_5_percent)

def on_match(matcher, doc, id, matches):
    unique_matches = set(matches)
    for id, start, end in unique_matches:
        match_text = doc[start:end].text
        print("Name:", match_text)

nlp = spacy.load('en_core_web_sm')    
matcher = Matcher(nlp.vocab)
patterns = [
    [{'POS': 'PROPN'}, {'POS': 'PROPN'}]
]
matcher.add("PERSON_NAME", patterns, on_match=on_match)
doc = nlp(first_5_percent)
matches = matcher(doc)

#email
def extract_email(email):
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", email)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None
email = extract_email(cleaned_text)
print("Email:", email)

def extract_mobile_number(text):
    phone = re.findall((r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'),text)
    for number in phone:
        print("Mobile number:", number)
mobile_number = extract_mobile_number(cleaned_text)

def extract_locations(text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    locations = []

    for entity in doc.ents:
        if entity.label_ == 'GPE':
            print("Location:", entity.text)
            break
locations = extract_locations(cleaned_text)

nlp = spacy.load('en_core_web_sm')


def extract_skills(text):
    nlp_text = nlp(text)

    tokens = [token.text for token in nlp_text if not token.is_stop and token.is_alpha and token.sent]
    #import your own data csv file
    data = pd.read_csv("sk.csv")
    skills = set(data['Skill'].str.lower().tolist())

    skillset = [token.capitalize() for token in tokens if token.lower() in skills]

    return list(set(skillset))  


skills = extract_skills(cleaned_text)
print("Skills:", skills)

def match_skills_with_job_domain(skills):
    #import your own data csv file
    data = pd.read_csv('job2.csv')

    skill_domain_mapping = {}
    job_domain_count = {}

    for index, row in data.iterrows():
        skill = row['Skill']
        job_domain = row['Job Domain']
        skill_domain_mapping[skill.lower()] = job_domain

        if job_domain not in job_domain_count:
            job_domain_count[job_domain] = 0

    matched_job_domains = []
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower in skill_domain_mapping:
            job_domain = skill_domain_mapping[skill_lower]
            matched_job_domains.append(job_domain)
            job_domain_count[job_domain] += 1

    job_domain_percentages = {}
    total_matched_skills = len(matched_job_domains)
    for job_domain in set(matched_job_domains):
        percentage = (job_domain_count[job_domain] / total_matched_skills) * 100
        job_domain_percentages[job_domain] = round(percentage, 2)

    return job_domain_percentages

matched_job_domains = match_skills_with_job_domain(skills)

print("Matched Job Domains:")
for job_domain, percentage in matched_job_domains.items():
    print("Job Domain:", job_domain ,":", percentage, "%")
