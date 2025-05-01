from datetime import datetime
import streamlit as st
import pandas as pd
import urllib.parse
import pandas as pd
import requests
import random
import string
import base64
import os
import re
import sys
import time


# Fix import path for the database module
# In frontend/app.py
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Now we can import from database module
from database.connection import init_database_tables

from database.operations import save_form_data, phone_exists_in_database, get_phone_occurrence_count

# Global constants
DEBUG_MODE = True

# Page setup
st.set_page_config(page_title="Customer Feedback Form", layout="wide")
st.session_state['DEBUG_MODE'] = DEBUG_MODE



# Function to safely reset form data while preserving branch
def reset_form_data():
    st.session_state.form_data = {}
    

# Initialize session state for form data and current page
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'language' not in st.session_state:
    st.session_state.language = 'English'
if 'temp_inputs' not in st.session_state:
    st.session_state.temp_inputs = {}
if 'nps_selected' not in st.session_state:
    st.session_state.nps_selected = None
if 'previous_page' not in st.session_state:
    st.session_state.previous_page = None
if 'branch' not in st.session_state:
    st.session_state.branch = None
# OTP verification states
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'otp_verified' not in st.session_state:
    st.session_state.otp_verified = False
if 'otp_code' not in st.session_state:
    st.session_state.otp_code = None
if 'otp_entry_page' not in st.session_state:
    st.session_state.otp_entry_page = False
if 'otp_verification_status' not in st.session_state:
    st.session_state.otp_verification_status = None


# SMS Service Credentials
SMS_API_URL = "https://restapi.tobeprecisesms.com/api"#st.secrets["SMS_API_URL"]
SMS_USERNAME = "AjmalOTP"#st.secrets["SMS_USERNAME"]
SMS_PASSWORD = "AJmt6301"#st.secrets["SMS_PASSWORD"]
SMS_SENDER = "Ajmal One"#st.secrets["SMS_SENDER"]


# ============== UTILITY FUNCTIONS ==============

def is_valid_email(email):
    """Check if email contains @ and ends with .com"""
    return '@' in email and email.lower().endswith('.com')

def update_text_input(field_name):
    """Save text input value to form data as user types"""
    if st.session_state[field_name]:
        st.session_state.form_data[field_name] = st.session_state[field_name]
        st.session_state.temp_inputs[field_name] = st.session_state[field_name]

def update_email_input():
    """Save email input with validation"""
    email = st.session_state.email
    if email:
        # Store the email in temp inputs even if invalid
        st.session_state.temp_inputs['email'] = email
        
        # Only store in form_data if valid
        if is_valid_email(email):
            st.session_state.form_data['email'] = email
        else:
            # Remove from form_data if it was previously valid but now invalid
            if 'email' in st.session_state.form_data:
                del st.session_state.form_data['email']

def generate_otp():
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))

def send_sms_otp(phone_number, otp_code):
    """Send OTP via SMS using the specified API"""
    # Format the message
    message = f"Your Ajmal Feedback Form verification code is: {otp_code}"
    
    # The API endpoint
    url = f"{SMS_API_URL}/SendSMS/SingleSMS/?Username={SMS_USERNAME}&Password={SMS_PASSWORD}"
    
    # Prepare the request data
    payload = {
        "Message": message,
        "MobileNumbers": phone_number,
        "SenderName": SMS_SENDER
    }
    
    try:
        # Make the POST request
        response = requests.post(url, data=payload, timeout=10)
        
        # For debugging purposes only, log to console instead of showing to user
        if DEBUG_MODE:
            print(f"SMS API response: {response.status_code}")
            if hasattr(response, 'content') and response.content:
                print(f"Response content: {response.text[:200]}")
        
        # Check if successful based on status code
        if response.status_code == 200:
            # Even with 200, check the content for error messages
            if "error" in response.text.lower() or "authorization error" in response.text.lower():
                if DEBUG_MODE:
                    print(f"API Error: Authentication failed")
                return False, "Error sending OTP. Please try again or use test mode."
            return True, "OTP sent successfully!"
        else:
            if DEBUG_MODE:
                print(f"Error sending OTP: Status code {response.status_code}")
            return False, f"Error sending OTP. Please try again."
    except Exception as e:
        if DEBUG_MODE:
            print(f"Exception sending OTP: {str(e)}")
        return False, f"Error sending OTP: {str(e)}"

def generate_gift_code():
    """Generate a unique gift code for first-time visitors"""
    # Format: AJM-[Random 6 digits]
    return f"AJM-{''.join(random.choices(string.digits, k=6))}"

def send_gift_code_sms(phone_number, gift_code):
    """Send gift code via SMS using the specified API"""
    # Format the message
    message = f"Thank you for visiting Ajmal! Here is your special gift code: {gift_code}. Present this code at any Ajmal store in the UAE to claim your gift."
    
    # The API endpoint
    url = f"{SMS_API_URL}/SendSMS/SingleSMS/?Username={SMS_USERNAME}&Password={SMS_PASSWORD}"
    
    # Prepare the request data
    payload = {
        "Message": message,
        "MobileNumbers": phone_number,
        "SenderName": SMS_SENDER
    }
    
    try:
        # In test mode, don't actually try to send SMS
        if st.session_state.get('test_mode', False):
            return True, "Gift code generated!"
        
        # Make the POST request
        response = requests.post(url, data=payload, timeout=10)
        
        # For debugging only, log to console
        if DEBUG_MODE:
            print(f"Gift code SMS API response: {response.status_code}")
        
        # Check if successful based on status code
        if response.status_code == 200:
            return True, "Gift code sent successfully!"
        else:
            # Don't show error to user, just log it
            if DEBUG_MODE:
                print(f"Error sending gift code SMS: {response.status_code} - {response.text}")
            return False, "We've generated your gift code!"
    except Exception as e:
        if DEBUG_MODE:
            print(f"Exception sending gift code SMS: {str(e)}")
        return False, "We've generated your gift code!"

def format_uae_number(phone_number):
    """Validate and format UAE phone number"""
    # Remove any spaces, dashes or parentheses
    phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # Check if it's already in international format
    if phone_number.startswith('+971'):
        return phone_number
    
    # If it starts with 0, replace with +971
    if phone_number.startswith('0'):
        return '+971' + phone_number[1:]
    
    # If it starts with 971 (without +), add +
    if phone_number.startswith('971'):
        return '+' + phone_number
    
    # If it's just the number without any prefix
    if len(phone_number) == 9 and phone_number.startswith(('50', '54', '55', '56', '58')):
        return '+971' + phone_number
    
    # Invalid format
    return None

def get_base64_image(image_path):
    """Convert an image to base64 encoding"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error loading image: {str(e)}")
    # Return a blank transparent image as fallback
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

def show_thank_you_page():
    """Display the thank you page after form submission"""
    # Display base thank you message
    st.markdown(get_text('thank_you_title'))
    st.markdown(get_text('thank_you_message'))
    
    # Add spacing
    st.write("")
    
    # Get the phone number
    phone_number = st.session_state.form_data.get('phone', '')
    
    if phone_number:
        # Get count of this phone number's occurrences in the database
        # Note: At this point, the current submission is already in the database
        # So a count of 1 means this is their first submission
        phone_count = get_phone_occurrence_count(phone_number)
        
        if DEBUG_MODE:
            print(f"Phone {phone_number} found {phone_count} times in database")
            
        # Only display gift message if this is exactly the 2nd time the phone is used (count = 1)
        # Count = 1 after saving the form means this is their 2nd submission overall
        if phone_count == 1:
            # Generate a gift code if not already generated
            if 'gift_code' not in st.session_state:
                gift_code = generate_gift_code()
                st.session_state.gift_code = gift_code
                
                # Send gift code SMS
                st.session_state.test_mode = 'test_otp' in st.session_state and st.session_state.test_otp
                send_gift_code_sms(phone_number, gift_code)
                
                if DEBUG_MODE:
                    print(f"Sent gift code {gift_code} to phone {phone_number} on their 2nd submission")
            
            # Display gift message for phone numbers on their 2nd submission
            st.markdown(get_text('gift_message'))
        elif DEBUG_MODE:
            if phone_count < 1:
                print(f"Phone {phone_number} is new (shouldn't happen since form just saved)")
            else:
                print(f"Phone {phone_number} has been used {phone_count} times - not showing gift message")
    
    # Add spacing
    st.write("")
    
    # Display closing message
    st.markdown(get_text('closing_message'))
    
    # Add spacing before button
    st.write("")
    st.write("")
    
    # Submit another response button
    if st.button(get_text('submit_another')):
        # Complete reset of all form related session state
        for key in list(st.session_state.keys()):
            if key in ['page', 'form_data', 'submitted', 'temp_inputs', 
                      'otp_sent', 'otp_verified', 'otp_code', 'otp_entry_page', 
                      'gift_code', 'test_mode', 'nps_selected', 'previous_page']:
                del st.session_state[key]
        
        # Reinitialize essential states with defaults
        st.session_state.page = 1
        st.session_state.form_data = {}
        st.session_state.submitted = False
        st.session_state.temp_inputs = {}
        st.session_state.otp_verified = False
        st.session_state.otp_sent = False
        st.session_state.otp_entry_page = False
        
        st.rerun()

# ============== TRANSLATIONS ==============

# Translations and text content
TRANSLATIONS = {
    'English': {
        # Page 1
        'language_selection': "Language Selection / اختيار اللغة",
        'select_language': "Please select your preferred language / يرجى اختيار لغتك المفضلة",
        
        # Page 2
        'first_visit': "Is this your first visit to an Ajmal Store?",
        'yes': "Yes",
        'no': "No",
        
        # Page 3
        'satisfaction': "Are you satisfied with your recent shopping experience?",
        
        # Page 4 - Satisfaction
        'satisfaction_reason': "Which of the following aspects of your experience you found most satisfactory?",
        'satisfaction_options': [
            "I found exactly what I was looking for",
            "I was happy with the price and promotions",
            "The store staff were very helpful and provided good customer service",
            "All of the above",
            "Other"
        ],
        
        # Page 4 - Dissatisfaction
        'dissatisfaction_reason': "Which of the following aspects of your experience did you find unsatisfactory?",
        'dissatisfaction_options': ["Product", "Staff", "Ambience", "Other"],
        
        # Page 5 - Satisfaction additional feedback
        'additional_feedback': "Would you like to share any additional feedback related to your recent shopping experience?",
        
        # Page 5 - Dissatisfaction specific reason
        'specific_reason': "Please specify your reason:",
        'select_specific_reason': "Please select one or more of the reasons listed below:",
        
        # Specific reason options by category
        'product_reasons': [
            "Not enough variety",
            "No offers or promotions on selected products",
            "The prices were higher than expected",
            "My preferred item was out of stock"
        ],
        'staff_reasons': [
            "Staff was not available to assist",
            "Staff was not willing to help",
            "Staff did not understand my requirements",
            "Staff was not welcoming and approachable"
        ],
        'ambience_reasons': [
            "It was too warm / too cold in the store",
            "The store and display seemed untidy",
            "The lighting was too bright / too dim",
            "The store layout was not very easy to navigate"
        ],
        
        # Page 6 - Dissatisfaction additional feedback
        'dissatisfaction_feedback': "We regret having missed the opportunity in providing you with a pleasant shopping experience. Please feel free to share any additional feedback related to your recent experience.",
        
        # Page 7 - NPS
        'nps_title': "NPS",
        'nps_question': "Based on your most recent experience, how likely are you to recommend us to your friends, family or colleagues?",
        'not_likely': "Not at all likely",
        'extremely_likely': "Extremely Likely",
        'selected_rating': "Selected Rating",
        
        # Page 8 - Contact info
        'contact_info': "Your Information",
        'full_name': "Full Name",
        'email': "Email Address",
        'invalid_email': "Please enter a valid email",
        'phone': "Phone Number (Verified)",
        
        # OTP Verification
        'mobile_verification': "Mobile Verification",
        'enter_phone': "Enter your UAE mobile number",
        'invalid_phone': "Invalid UAE mobile number format. Please check your input.",
        'phone_formatted': "Your number will be formatted as:",
        'send_otp': "Send OTP",
        'enter_verification': "Enter Verification Code",
        'code_sent': "A verification code has been sent to:",
        'enter_otp': "Enter OTP",
        'back': "← Back",
        'verify_otp': "Verify OTP",
        'otp_success': "OTP verified! You can now proceed with the feedback form.",
        'otp_error': "Invalid OTP. Please check and try again.",
        
        # Navigation
        'previous': "← Previous",
        'next': "Next →",
        'submit': "Submit Feedback",
        'name_error': "Please fill in your name",
        'email_error': "Please enter a valid email address",
        'submit_another': "Submit Another Response",
        
        # Thank you page
        'thank_you_title': "# Thank You for Your Valuable Feedback!",
        'thank_you_message': "We greatly appreciate you taking the time to share your experience with us. Your feedback helps us improve our services.",
        'gift_message': "As a token of gratitude, we are pleased to offer you a special gift. Show the SMS with the unique gift code at any Ajmal store across the UAE to claim your gift.",
        'closing_message': "Have a great day!"
    },
    'Arabic': {
        # Page 1
        'language_selection': "Language Selection / اختيار اللغة",
        'select_language': "Please select your preferred language / يرجى اختيار لغتك المفضلة",
        
        # Page 2
        'first_visit': "هل هذه زيارتك الأولى لمتجر أجمل؟",
        'yes': "نعم",
        'no': "لا",
        
        # Page 3
        'satisfaction': "هل أنت راضٍ عن تجربة التسوق الأخيرة التي قمت بها؟",
        
        # Page 4 - Satisfaction
        'satisfaction_reason': "أي من الجوانب التالية من تجربتك وجدتها أكثر إرضاءً؟",
        'satisfaction_options': [
            "قد وجدت بالضبط ما كنت أبحث عنه",
            "كنت سعيدًا بالسعر والعروض الترويجية",
            "كنت سعيداً بمستوى خدمة العملاء",
            "كل ما سبق",
            "أخرى"
        ],
        
        # Page 4 - Dissatisfaction
        'dissatisfaction_reason': "أي من الجوانب التالية من تجربتك وجدتها غير مرضية؟",
        'dissatisfaction_options': ["المنتج", "الموظفين", "الأجواء", "أخرى"],
        
        # Page 5 - Satisfaction additional feedback
        'additional_feedback': "هل ترغب في مشاركة أي ملاحظات إضافية تتعلق بتجربة تسوقك الأخيرة؟",
        
        # Page 5 - Dissatisfaction specific reason
        'select_specific_reason': "يرجى اختيار أحد الأسباب المذكورة أدنا:",
        
        # Specific reason options by category
        'product_reasons': [
            "لا يوجد تنوع كافٍ",
            "لا توجد عروض على المنتجات المفضلة لي",
            "الأسعار كانت أعلى من المتوقع",
            "كان إختياري المفضل غير متوفر"
        ],
        'staff_reasons': [
            "لم يكن الموظفون متاحين للمساعدة",
            "لم يكن الموظفون على استعداد للمساعدة",
            "لم يفهم الموظفون متطلباتي",
            "لم يكن الموظفون مرحبين و ودودين"
        ],
        'ambience_reasons': [
            "كان الجو حاراً جدًا / باردًا جدًا في المتجر",
            "المتجر وكيفية عرض المنتجات كانت غير مرتبة",
            "كانت الإضاءة ساطعة جدًا / خافتة جدًا",
            "تصميم المتجر يجعل التنقل ليس سهلاً  "
        ],
        
        # Page 6 - Dissatisfaction additional feedback
        'dissatisfaction_feedback': "نأسف لإضاعة الفرصة لتزويدك بتجربة تسوق ممتعة لا تتردد في مشاركة أي تعليقات إضافية تتعلق بتجربتك الأخيرة",
        
        # Page 7 - NPS
        'nps_title': "مقياس صافي نقاط الترويج",
        'nps_question': "بناءً على تجربتك الأخيرة، ما مدى احتمالية أن توصي بنا لأصدقائك أو عائلتك أو زملائك؟",
        'not_likely': "ليس من المحتمل على الإطلاق",
        'extremely_likely': "محتمل للغاية",
        'selected_rating': "التقييم المحدد",
        
        # Page 8 - Contact info
        'contact_info': "معلوماتك",
        'full_name': "الاسم الكامل",
        'email': "عنوان البريد الإلكتروني",
        'invalid_email': "يرجى إدخال بريد إلكتروني صحيح (يجب أن يحتوي على @ وينتهي بـ .com)",
        'phone': "رقم الهاتف (تم التحقق)",
        
        # OTP Verification
        'mobile_verification': "التحقق من الهاتف المحمول",
        'enter_phone': "أدخل رقم هاتفك المحمول الإماراتي",
        'invalid_phone': "صيغة رقم الهاتف غير صالحة. يرجى التحقق من رقمك.",
        'phone_formatted': "سيتم تنسيق رقمك كالتالي:",
        'send_otp': "إرسال رمز التحقق",
        'enter_verification': "أدخل رمز التحقق",
        'code_sent': "تم إرسال رمز التحقق إلى:",
        'enter_otp': "أدخل رمز التحقق",
        'back': "← رجوع",
        'verify_otp': "تحقق",
        'otp_success': "تم التحقق بنجاح! يمكنك الآن المتابعة مع استمارة التعليقات.",
        'otp_error': "رمز التحقق غير صحيح. يرجى التحقق والمحاولة مرة أخرى.",
        
        # Navigation
        'previous': "← السابق",
        'next': "التالي →",
        'submit': "إرسال التعليقات",
        'name_error': "يرجى تعبئة اسمك",
        'email_error': "يرجى إدخال بريد إلكتروني صحيح",
        'submit_another': "إرسال استجابة أخرى",
        
        # Thank you page
        'thank_you_title': "# !شكراً على ملاحظاتك القيمة",
        'thank_you_message': ".نقدر لك الوقت الذي قضيته في مشاركة تجربتك معنا. ملاحظاتك تساعدنا على تحسين خدماتنا",
        'gift_message': ".كرمز للامتنان، يسرنا أن نقدم لك هدية خاصة. اعرض الرسالة النصية مع رمز الهدية الفريد في أي متجر أجمل في الإمارات العربية المتحدة للحصول على هديتك",
        'closing_message': "!نتمنى لك يوماً سعيداً"
    }
}


# Translation mapping (from English to Arabic and vice versa)
TRANSLATIONS_MAPPING = {
    'satisfaction_options': {
        'English_to_Arabic': {
            "I found exactly what I was looking for": "وجدت بالضبط ما كنت أبحث عنه",
            "I was happy with the price and promotions": "كنت سعيداً بالسعر والعروض الترويجية",
            "The store staff were very helpful and provided good customer service": "كان موظفو المتجر متعاونين جداً وقدموا خدمة عملاء جيدة",
            "All of the above": "كل ما سبق",
            "Other": "أخرى"
        },
        'Arabic_to_English': {
            "وجدت بالضبط ما كنت أبحث عنه": "I found exactly what I was looking for",
            "كنت سعيداً بالسعر والعروض الترويجية": "I was happy with the price and promotions",
            "كان موظفو المتجر متعاونين جداً وقدموا خدمة عملاء جيدة": "The store staff were very helpful and provided good customer service",
            "كل ما سبق": "All of the above",
            "أخرى": "Other"
        }
    },
    'dissatisfaction_options': {
        'English_to_Arabic': {
            "Product": "المنتج",
            "Staff": "الموظفين",
            "Ambience": "الأجواء",
            "Other": "أخرى"
        },
        'Arabic_to_English': {
            "المنتج": "Product",
            "الموظفين": "Staff",
            "الأجواء": "Ambience",
            "أخرى": "Other"
        }
    },
    'yes_no': {
        'English_to_Arabic': {
            "Yes": "نعم",
            "No": "لا"
        },
        'Arabic_to_English': {
            "نعم": "Yes",
            "لا": "No"
        }
    }
}

def get_text(key):
    """Get translated text based on current language"""
    lang = st.session_state.language
    return TRANSLATIONS[lang].get(key, key)

def get_options(key):
    """Get translated options based on current language"""
    lang = st.session_state.language
    return TRANSLATIONS[lang].get(key, [])

# ============== FORM PAGE RENDERING FUNCTIONS ==============

def render_satisfaction_reason():
    """Render page 4: Satisfaction reason"""
    question = get_text('satisfaction_reason')
    options = get_options('satisfaction_options')
    
    # Get previously selected value if any
    satisfaction_reason_index = None
    if 'satisfaction_reason' in st.session_state.form_data:
        selected_val = st.session_state.form_data['satisfaction_reason']
        # Map English values to Arabic if language is Arabic
        if st.session_state.language == 'Arabic':
            eng_to_ar = {
                "I found exactly what I was looking for": "وجدت بالضبط ما كنت أبحث عنه",
                "I was happy with the price and promotions": "كنت سعيداً بالسعر والعروض الترويجية",
                "The store staff were very helpful and provided good customer service": "كان موظفو المتجر متعاونين جداً وقدموا خدمة عملاء جيدة",
                "All of the above": "كل ما سبق",
                "Other": "أخرى"
            }
            selected_val = eng_to_ar.get(selected_val, selected_val)
        try:
            satisfaction_reason_index = options.index(selected_val)
        except ValueError:
            satisfaction_reason_index = None
    
    st.markdown(f"###### {question}")
    satisfaction_reason = st.radio(
        "",
        options, 
        key="satisfaction_reason",
        index=satisfaction_reason_index
    )
    if satisfaction_reason:
        # Store in English for consistent processing
        if st.session_state.language == 'Arabic':
            ar_to_en = {
                "وجدت بالضبط ما كنت أبحث عنه": "I found exactly what I was looking for",
                "كنت سعيداً بالسعر والعروض الترويجية": "I was happy with the price and promotions",
                "كان موظفو المتجر متعاونين جداً وقدموا خدمة عملاء جيدة": "The store staff were very helpful and provided good customer service",
                "كل ما سبق": "All of the above",
                "أخرى": "Other"
            }
            st.session_state.form_data['satisfaction_reason'] = ar_to_en.get(satisfaction_reason, satisfaction_reason)
        else:
            st.session_state.form_data['satisfaction_reason'] = satisfaction_reason

def render_dissatisfaction_reason():
    """Render page 4: Dissatisfaction reason"""
    question = get_text('dissatisfaction_reason')
    options = get_options('dissatisfaction_options')
    
    # Get previously selected value if any
    dissatisfaction_reason_index = None
    if 'dissatisfaction_reason' in st.session_state.form_data:
        selected_val = st.session_state.form_data['dissatisfaction_reason']
        # Map English values to Arabic if language is Arabic
        if st.session_state.language == 'Arabic':
            eng_to_ar = {
                "Product": "المنتج",
                "Staff": "الموظفين",
                "Ambience": "الأجواء",
                "Other": "أخرى"
            }
            selected_val = eng_to_ar.get(selected_val, selected_val)
        try:
            dissatisfaction_reason_index = options.index(selected_val)
        except ValueError:
            dissatisfaction_reason_index = None
    
    st.markdown(f"##### {question}")
    dissatisfaction_reason = st.radio(
        "",
        options, 
        key="dissatisfaction_reason",
        index=dissatisfaction_reason_index
    )
    if dissatisfaction_reason:
        # Convert to English for consistent storage
        if st.session_state.language == 'Arabic':
            ar_to_en = {
                "المنتج": "Product",
                "الموظفين": "Staff",
                "الأجواء": "Ambience",
                "أخرى": "Other"
            }
            st.session_state.form_data['dissatisfaction_reason'] = ar_to_en.get(dissatisfaction_reason, dissatisfaction_reason)
        else:
            st.session_state.form_data['dissatisfaction_reason'] = dissatisfaction_reason

def render_satisfaction_feedback():
    """Render page 5: Additional feedback for satisfied customers"""
    question = get_text('additional_feedback')
    st.markdown(f"##### {question}")
    
    # Load previously entered feedback if available
    default_value = st.session_state.form_data.get('feedback', st.session_state.temp_inputs.get('feedback', ''))
    
    # Use on_change handler to save input as user types
    st.text_area("", key="feedback", value=default_value, on_change=update_text_input, args=('feedback',))

def render_specific_reason_other():
    """Render page 5: Specific reason for 'Other' dissatisfaction"""
    question = get_text('specific_reason')
    st.markdown(f"##### {question}")
    feedback = st.text_area("", key="specific_reason")
    if feedback:
        st.session_state.form_data['specific_reason'] = feedback

def render_specific_reason_category():
    """Render page 5: Specific reason for category-based dissatisfaction"""
    reason_type = st.session_state.form_data.get('dissatisfaction_reason')
    
    # Select appropriate options based on reason type
    reason_key = f"{reason_type.lower()}_reasons"
    options = get_options(reason_key)
    
    question = get_text('select_specific_reason')
    st.markdown(f"##### {question}")
    
    # Get previously selected value if any
    specific_reason_index = None
    if 'specific_reason' in st.session_state.form_data:
        selected_val = st.session_state.form_data['specific_reason']
        
        # Map to current language for display if needed
        if st.session_state.language == 'Arabic':
            # Find the English-to-Arabic mapping that matches this reason type
            option_mappings = {}
            for i, option in enumerate(TRANSLATIONS['English'][reason_key]):
                arabic_option = TRANSLATIONS['Arabic'][reason_key][i] if i < len(TRANSLATIONS['Arabic'][reason_key]) else option
                option_mappings[option] = arabic_option
                
            selected_val = option_mappings.get(selected_val, selected_val)
        
        try:
            specific_reason_index = options.index(selected_val)
        except ValueError:
            specific_reason_index = None
    
    specific_reason = st.radio(
        "",
        options, 
        key="specific_reason",
        index=specific_reason_index
    )
    
    if specific_reason:
        # Convert back to English for storage if needed
        if st.session_state.language == 'Arabic':
            # Find the Arabic-to-English mapping
            option_mappings = {}
            for i, option in enumerate(TRANSLATIONS['Arabic'][reason_key]):
                english_option = TRANSLATIONS['English'][reason_key][i] if i < len(TRANSLATIONS['English'][reason_key]) else option
                option_mappings[option] = english_option
                
            st.session_state.form_data['specific_reason'] = option_mappings.get(specific_reason, specific_reason)
        else:
            st.session_state.form_data['specific_reason'] = specific_reason

def render_dissatisfaction_feedback():
    """Render page 6: Additional feedback for dissatisfied customers"""
    question = get_text('dissatisfaction_feedback')
    st.markdown(f"##### {question}")
    
    # Load previously entered feedback if available
    default_value = st.session_state.form_data.get('feedback', st.session_state.temp_inputs.get('feedback', ''))
    
    # Use on_change handler to save input as user types
    st.text_area("", key="feedback", value=default_value, on_change=update_text_input, args=('feedback',))

def render_nps_rating():
    """Render page 7: NPS rating"""
    title = get_text('nps_title')
    st.markdown(f"### {title}")
    
    question = get_text('nps_question')
    st.markdown(f"##### {question}")

    # Get the currently selected NPS value
    selected_nps = st.session_state.form_data.get('nps', None)
    
    # Create a container for the NPS buttons
    st.markdown('<div style="margin: 2rem 0;">', unsafe_allow_html=True)
    
    # Check if rating buttons are clicked
    cols = st.columns(11)
    for i in range(11):
        with cols[i]:
            # Add the appropriate CSS class based on the button number
            button_class = f"nps-button-{i}"
            if selected_nps == i:
                button_class += " nps-button-selected"
            
            # Create the button with streamlit and the appropriate class
            if st.button(str(i), key=f"nps_{i}", help=button_class):
                st.session_state.form_data['nps'] = i
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Add some vertical spacing
    st.write("")
    
    # Display labels under the scale with CSS classes
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='nps-label-left'>{}</div>".format(
            get_text('not_likely')
        ), unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='nps-label-right'>{}</div>".format(
            get_text('extremely_likely')
        ), unsafe_allow_html=True)

    # Show the currently selected rating
    if selected_nps is not None:
        st.markdown(f"<div class='nps-selected-rating'>{get_text('selected_rating')}: {selected_nps}</div>", unsafe_allow_html=True)

def render_contact_info():
    """Render page 8: Contact information"""
    title = get_text('contact_info')
    st.markdown(f"### {title}")
    
    # Name field with saved value and on_change handler
    name_label = get_text('full_name')
    default_name = st.session_state.form_data.get('name', st.session_state.temp_inputs.get('name', ''))
    st.text_input(name_label, value=default_name, key='name', on_change=update_text_input, args=('name',))
    
    # Show name error if field is touched but empty
    if 'name' in st.session_state.temp_inputs and not st.session_state.form_data.get('name'):
        st.markdown(f'<p style="color: red; font-size: 0.8rem; margin-top: -1rem; margin-bottom: 1rem;">{get_text("name_error")}</p>', unsafe_allow_html=True)
        
    # Email field with validation and on_change handler
    email_label = get_text('email')
    default_email = st.session_state.form_data.get('email', st.session_state.temp_inputs.get('email', ''))
    email = st.text_input(email_label, value=default_email, key='email', on_change=update_email_input)
    
    # Show email error if invalid or missing
    if 'email' in st.session_state.temp_inputs:
        if not email:
            # Empty email
            st.markdown(f'<p style="color: red; font-size: 0.8rem; margin-top: -1rem; margin-bottom: 1rem;">{get_text("email_error")}</p>', unsafe_allow_html=True)
        elif not is_valid_email(email):
            # Invalid email format
            error_msg = get_text('invalid_email')
            st.markdown(f'<p style="color: red; font-size: 0.8rem; margin-top: -1rem; margin-bottom: 1rem;">{error_msg}</p>', unsafe_allow_html=True)
    
    # Display the verified phone number (read-only)
    phone_label = get_text('phone')
    verified_phone = st.session_state.form_data.get('phone', '')
    st.text_input(phone_label, value=verified_phone, disabled=True)

def is_current_field_valid():
    """Check if the current page's required fields are filled"""
    page = st.session_state.page
    
    if page == 1:
        return 'language' in st.session_state.form_data
    elif page == 2:
        return 'first_visit' in st.session_state.form_data
    elif page == 3:
        return 'satisfaction' in st.session_state.form_data
    elif page == 4:
        return ('satisfaction_reason' in st.session_state.form_data or 
                'dissatisfaction_reason' in st.session_state.form_data)
    elif page == 5:
        if st.session_state.form_data.get('satisfaction') == 'Yes':
            # For satisfied customers, feedback is optional but we need some value
            return 'feedback' in st.session_state.form_data
        else:
            return 'specific_reason' in st.session_state.form_data
    elif page == 6:
        if st.session_state.form_data.get('satisfaction') == 'No':
            # For dissatisfied customers, feedback is optional but we need some value
            return 'feedback' in st.session_state.form_data
        else:
            # For satisfied customers who skip to page 7
            return True
    elif page == 7:
        return 'nps' in st.session_state.form_data
    
    return False

def is_form_complete():
    """Check if all required fields for submission are complete"""
    name_valid = 'name' in st.session_state.form_data
    email_valid = 'email' in st.session_state.form_data
    
    return name_valid and email_valid

def handle_previous_navigation():
    """Handle the previous button navigation logic"""
    if st.session_state.page > 1:
        button_key = f"prev_button_page{st.session_state.page}"
        
        if st.button(get_text('previous'), key=button_key):
            # Handle special case for satisfied customers when going back from NPS page
            if st.session_state.page == 7 and st.session_state.form_data.get('satisfaction') == 'Yes':
                # Check if we need to go back to page 5 (feedback page) instead of page 6
                if 'feedback' in st.session_state.form_data:
                    st.session_state.page = 5
                else:
                    st.session_state.page = 4
            else:
                st.session_state.page -= 1
            st.rerun()

def handle_next_navigation():
    """Handle the next button navigation logic"""
    if st.session_state.page < 8:
        if st.button(get_text('next'), disabled=not is_current_field_valid()):
            st.session_state.page += 1
            st.rerun()
    else:
        # Submit button on the last page
        if st.button(get_text('submit'), disabled=not is_form_complete()):
            st.write(f"Selected Branch from nav: {st.session_state.form_data}")
            print("\n=== FORM SUBMISSION STARTED ===")
            print(f"Form data: {st.session_state.form_data}")
            
            # Add a spinner while processing submission
            with st.spinner("Processing your submission..."):
                try:
                    # Attempt to save using either SQLAlchemy or direct DB operations
                    # Always update branch in form_data before saving
                    st.session_state.form_data['branch'] = st.query_params.get("branch", None)

                    success = save_form_data(st.session_state.form_data)
                    print(f"Save result: {success}")
                    
                    if success:
                        st.session_state.submitted = True
                        print("Form marked as submitted")
                        st.rerun()
                    else:
                        # Only show error on failure
                        st.error("Failed to save your feedback. Please try again.")
                        print("Save operation reported failure")
                except Exception as e:
                    print(f"Error during submission: {str(e)}")
                
                    # Try direct database save as last resort
                    try:
                        from database.operations import direct_save_form_data
                        print("Last resort: trying direct database save")
                        success = direct_save_form_data(st.session_state.form_data)
                        
                        if success:
                            st.session_state.submitted = True
                            print("Emergency save successful")
                            st.rerun()
                        else:
                            st.error("Failed to save your feedback. Please try again.")
                    except Exception as e2:
                        print(f"Emergency save failed: {str(e2)}")
                        st.error("Failed to save your feedback. Please try again.")
            
            print("=== FORM SUBMISSION ENDED ===\n")

def set_branch_from_url():
    """Set branch from URL parameters or subdomain"""
    try:
        # Get the current URL from the query parameters
        current_url = st.query_params.get("_st_url", "")
        if current_url:
            # Extract subdomain from URL
            # Format: https://ajmalfeedback-dubai.streamlit.app
            subdomain = current_url.split("//")[1].split(".")[0]
            if subdomain and "ajmalfeedback-" in subdomain:
                return subdomain.replace("ajmalfeedback-", "")
    except Exception as e:
        print(f"Error extracting branch from URL: {str(e)}")
    return None

def main():
    """Main application function"""
    # Initialize database tables
    init_database_tables()
    
    # Get the absolute path to the parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Set branch from URL
    if not st.session_state.branch:
        branch = set_branch_from_url()
        if branch:
            st.session_state.branch = branch
            st.session_state.form_data['branch'] = branch
            print(f"Branch set to: {branch}")  # Debug print
    
    # Load CSS 
    # Custom CSS for styling
    st.markdown("""
    <style>
    /* Main container styling */
    .stApp {
        overflow: hidden;
        max-width: 800px;
        margin: 0 auto;
        padding: 0.2rem;
        height: 100vh;
    }
    /* Remove scrollbar */
    ::-webkit-scrollbar {
        display: none;
    }
    /* Logo container */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 2.5rem;
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        width: 100%;
    }

    .logo-img {
        height: 100px;
        max-width: 100%;
        object-fit: contain;
    }

    .stButton button {
        width: 100%;
        padding: 6px 12px;
        background-color: #464eb8;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        transition: all 0.3s ease;
        font-size: 0.85rem;
        margin: 0.2rem 0;
    }
    
    /* Smaller buttons for OTP */
    .small-button button {
        width: auto !important;
        min-width: 120px !important;
        max-width: 180px !important;
        display: inline-block !important;
    }
    
    .stButton button:hover {
        background-color: rgb(70,78,184);
        color: rgb(222, 221, 215);
    }
    /* Additional styles for OTP verification */
    .verification-container {
        border-top: 1px solid #ddd;
        padding: 20px;
        margin: 10px 0;
    }
    .verification-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 15px;
        color: #333;
        text-align: center;
    }
    .otp-input {
        font-size: 1.5rem;
        letter-spacing: 0.2rem;
        text-align: center;
    }
    /* NPS button styling */
    .nps-button-selected {
        border: 2px solid black !important;
        font-weight: bold !important;
    }
    .nps-label-left {
        text-align: left;
        font-size: 0.9rem;
        color: #333;
    }
    .nps-label-right {
        text-align: right;
        font-size: 0.9rem;
        color: #333;
    }
    .nps-selected-rating {
        text-align: center;
        margin-top: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render logo
    # Try to find the logo in possible locations
    logo_paths = [
        os.path.join(parent_dir, "static", "images", "ajmal_logo.png"),
        os.path.join("static", "images", "ajmal_logo.png"),
        os.path.join("..", "static", "images", "ajmal_logo.png")
    ]
    
    image_base64 = None
    for path in logo_paths:
        if os.path.exists(path):
            image_base64 = get_base64_image(path)
            break
    
    # Center the logo above questions
    if image_base64:
        st.markdown(f"""
        <div class='logo-container'>
            <img src='data:image/png;base64,{image_base64}' class='logo-img'>
        </div>
        """, unsafe_allow_html=True)
    
    # Add some spacing
    st.write("")

    # OTP Verification before showing the form
    if not st.session_state.otp_verified:
        # Use a container with just a top border instead of a full background container
        st.markdown("<div class='verification-container'>", unsafe_allow_html=True)
        
        # First page - Phone entry
        if not st.session_state.otp_sent and not st.session_state.otp_entry_page:
            st.markdown(f"<div class='verification-title'>{get_text('mobile_verification')}</div>", unsafe_allow_html=True)
            
            phone = st.text_input(get_text('enter_phone'))
            
            formatted_phone = format_uae_number(phone) if phone else None
            valid_phone = formatted_phone is not None and len(formatted_phone) >= 12
            
            if phone:
                if valid_phone:
                    st.success(f"{get_text('phone_formatted')} {formatted_phone}")
                    # Check if this phone number exists in the database
                    if phone_exists_in_database(formatted_phone):
                        st.info("This phone number has been used before. You can still continue with the form.")
                else:
                    st.error(get_text('invalid_phone'))
            
            # Use a smaller button for OTP sending
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.markdown("<div class='small-button'>", unsafe_allow_html=True)
                if st.button(get_text('send_otp'), disabled=not valid_phone):
                    # Generate a new OTP
                    otp_code = generate_otp()
                    st.session_state.otp_code = otp_code
                    
                    # Reset verification status
                    if 'otp_verification_status' in st.session_state:
                        st.session_state.otp_verification_status = None
                    
                    # Send OTP via SMS
                    success, message = send_sms_otp(formatted_phone, otp_code)
                    if success:
                        st.session_state.otp_sent = True
                        st.session_state.form_data['phone'] = formatted_phone
                        st.session_state.otp_entry_page = True
                        st.rerun()
                    else:
                        st.error(message)
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Second page - OTP Entry
        elif st.session_state.otp_sent or st.session_state.otp_entry_page:
            st.markdown(f"<div class='verification-title'>{get_text('enter_verification')}</div>", unsafe_allow_html=True)
            
            # Show which phone number the code was sent to
            phone_number = st.session_state.form_data.get('phone', '')
            st.markdown(f"{get_text('code_sent')} **{phone_number}**")
            
            # Centered OTP input with larger font
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                otp_input = st.text_input(get_text('enter_otp'), key="otp_input", placeholder="Enter the 6-digit code")
                
                # Show OTP verification messages directly under the input field
                if 'otp_verification_status' in st.session_state:
                    if st.session_state.otp_verification_status == 'success':
                        st.success(get_text('otp_success'))
                    elif st.session_state.otp_verification_status == 'error':
                        st.error(get_text('otp_error'))
            
            # Verify and Back buttons
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col2:
                st.markdown("<div class='small-button'>", unsafe_allow_html=True)
                back_clicked = st.button(get_text('back'))
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col3:
                st.markdown("<div class='small-button'>", unsafe_allow_html=True)
                verify_clicked = st.button(get_text('verify_otp'))
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Handle OTP verification
            if verify_clicked:
                if otp_input == st.session_state.otp_code:
                    # Success
                    st.session_state.otp_verification_status = 'success'
                    st.session_state.otp_verified = True
                    time.sleep(1)  # Short delay to show success message
                    st.rerun()
                else:
                    # Error
                    st.session_state.otp_verification_status = 'error'
                    st.rerun()
            
            # Handle back button
            if back_clicked:
                st.session_state.otp_entry_page = False
                st.session_state.otp_sent = False
                if 'otp_verification_status' in st.session_state:
                    del st.session_state.otp_verification_status
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        return  # Exit the function if not verified

    # If form is submitted, show thank you page
    if st.session_state.submitted:
        show_thank_you_page()
        return

    # Progress bar calculation
    max_pages = 8  # Total maximum possible pages
    progress = min((st.session_state.page - 1) / (max_pages - 1), 1.0)
    progress_bar = st.progress(progress)

    # Render the appropriate page based on the current page number
    if st.session_state.page == 1:
        # Language selection page
        st.markdown(f"### {get_text('language_selection')}")
        language_options = ["English", "Arabic"]
        
        # Get index of previously selected language
        language_index = None
        if 'language' in st.session_state.form_data:
            try:
                language_index = language_options.index(st.session_state.form_data['language'])
            except ValueError:
                language_index = None
        
        language = st.radio(
            get_text('select_language'),
            language_options,
            index=language_index
        )
        if language:
            st.session_state.language = language
            st.session_state.form_data['language'] = language
    
    elif st.session_state.page == 2:
        # First visit question
        question = get_text('first_visit')
        st.markdown(f"##### {question}")
        
        options = [get_text('yes'), get_text('no')]
        
        # Get previously selected value if any
        first_visit_index = None
        if 'first_visit' in st.session_state.form_data:
            selected_val = st.session_state.form_data['first_visit']
            # Map English values to Arabic if language is Arabic
            if st.session_state.language == 'Arabic':
                eng_to_ar = {"Yes": "نعم", "No": "لا"}
                selected_val = eng_to_ar.get(selected_val, selected_val)
            try:
                first_visit_index = options.index(selected_val)
            except ValueError:
                first_visit_index = None
        
        first_visit = st.radio(
            "",
            options,
            key="first_visit",
            index=first_visit_index
        )
        if first_visit:
            # Convert to English for consistent storage
            if st.session_state.language == 'Arabic':
                ar_to_en = {"نعم": "Yes", "لا": "No"}
                st.session_state.form_data['first_visit'] = ar_to_en.get(first_visit, first_visit)
            else:
                st.session_state.form_data['first_visit'] = first_visit
    
    elif st.session_state.page == 3:
        # Satisfaction question
        question = get_text('satisfaction')
        st.markdown(f"##### {question}")
        
        options = [get_text('yes'), get_text('no')]
        
        # Get previously selected value if any
        satisfaction_index = None
        if 'satisfaction' in st.session_state.form_data:
            selected_val = st.session_state.form_data['satisfaction']
            # Map English values to Arabic if language is Arabic
            if st.session_state.language == 'Arabic':
                eng_to_ar = {"Yes": "نعم", "No": "لا"}
                selected_val = eng_to_ar.get(selected_val, selected_val)
            try:
                satisfaction_index = options.index(selected_val)
            except ValueError:
                satisfaction_index = None
        
        satisfaction = st.radio(
            "",
            options,
            key="satisfaction",
            index=satisfaction_index
        )
        if satisfaction:
            # Convert to English for consistent storage
            if st.session_state.language == 'Arabic':
                ar_to_en = {"نعم": "Yes", "لا": "No"}
                st.session_state.form_data['satisfaction'] = ar_to_en.get(satisfaction, satisfaction)
            else:
                st.session_state.form_data['satisfaction'] = satisfaction
    
    elif st.session_state.page == 4:
        if st.session_state.form_data.get('satisfaction') == 'Yes':
            # Satisfaction reason
            render_satisfaction_reason()
        else:
            # Dissatisfaction reason
            render_dissatisfaction_reason()
    
    elif st.session_state.page == 5:
        if st.session_state.form_data.get('satisfaction') == 'Yes':
            # Additional feedback for satisfied customers
            render_satisfaction_feedback()
        elif st.session_state.form_data.get('dissatisfaction_reason') == 'Other':
            # Specific reason for 'Other' dissatisfaction
            render_specific_reason_other()
        else:
            # Specific reason for category-based dissatisfaction
            render_specific_reason_category()
    
    elif st.session_state.page == 6:
        if st.session_state.form_data.get('satisfaction') == 'No':
            # Additional feedback for dissatisfied customers
            render_dissatisfaction_feedback()
        else:
            # Skip to next page if satisfied customer
            st.session_state.previous_page = 6
            st.session_state.page += 1
            st.rerun()
    
    elif st.session_state.page == 7:
        # NPS rating
        render_nps_rating()
    
    elif st.session_state.page == 8:
        # Contact information
        render_contact_info()
    
    # Navigation buttons
    st.write("")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        handle_previous_navigation()
    
    # Empty column in the middle
    with col2:
        pass
            
    with col3:
        handle_next_navigation()

if __name__ == "__main__":
    main() 
