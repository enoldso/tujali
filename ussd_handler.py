import logging
from models import Patient, Provider, Appointment, Message, HealthInfo
from datetime import datetime, timedelta
import utils

# Configure logging
logger = logging.getLogger(__name__)

# Session storage for USSD
# This is used to keep track of user state between USSD requests
# In production, this should be stored in a database or cache
sessions = {}

def ussd_callback(session_id, service_code, phone_number, text):
    """
    Process USSD request and return appropriate response
    
    Args:
        session_id (str): Unique session identifier
        service_code (str): USSD service code
        phone_number (str): User's phone number
        text (str): Current USSD text/input
    
    Returns:
        str: USSD response with appropriate prefix
    """
    # Initialize session if needed
    if session_id not in sessions:
        sessions[session_id] = {
            'phone_number': phone_number,
            'state': 'start',
            'language': 'en',  # Default language
            'data': {}
        }
    
    session = sessions[session_id]
    
    # Check if we need to start over
    if text == '':
        session['state'] = 'start'
        session['data'] = {}
    
    # Handle language selection first if not already set
    if session['state'] == 'start':
        response = "Welcome to Tujali Telehealth\n"
        response += "Karibu kwenye Tujali Telehealth\n"
        response += "Bienvenue sur Tujali Telehealth\n"
        response += "Soo dhawow Tujali Telehealth\n"
        response += "1. English\n"
        response += "2. Kiswahili\n"
        response += "3. Français (French)\n"
        response += "4. Afaan Oromoo (Oromo)\n"
        response += "5. Soomaali (Somali)\n"
        response += "6. Amharic (አማርኛ)"
        session['state'] = 'select_language'
        return respond(response)
    
    elif session['state'] == 'select_language':
        if text == '1' or text.endswith('*1'):
            session['language'] = 'en'
            return show_main_menu(session)
        elif text == '2' or text.endswith('*2'):
            session['language'] = 'sw'
            return show_main_menu(session)
        elif text == '3' or text.endswith('*3'):
            session['language'] = 'fr'
            return show_main_menu(session)
        elif text == '4' or text.endswith('*4'):
            session['language'] = 'om'
            return show_main_menu(session)
        elif text == '5' or text.endswith('*5'):
            session['language'] = 'so'
            return show_main_menu(session)
        elif text == '6' or text.endswith('*6'):
            session['language'] = 'am'
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    # Process based on current state
    if text.endswith('*0'):  # Return to main menu from anywhere
        return show_main_menu(session)
    
    # Get the last input from the user
    parts = text.split('*')
    last_input = parts[-1] if parts else ''
    
    # Route to appropriate handler based on state
    try:
        if session['state'] == 'main_menu':
            return handle_main_menu(session, last_input)
        elif session['state'].startswith('register'):
            return handle_registration(session, last_input)
        elif session['state'].startswith('symptom'):
            return handle_symptoms(session, last_input)
        elif session['state'].startswith('appointment'):
            return handle_appointments(session, last_input)
        elif session['state'].startswith('message'):
            return handle_messages(session, last_input)
        elif session['state'].startswith('profile') or session['state'].startswith('update_coordinates') or session['state'].startswith('coordinates_updated'):
            return handle_messages(session, last_input)
        elif session['state'].startswith('info'):
            return handle_health_info(session, last_input)
        else:
            # Unknown state, return to main menu
            return show_main_menu(session)
    except Exception as e:
        logger.error(f"Error processing USSD request: {e}")
        
        # Provide error messages in all supported languages
        if session['language'] == 'en':
            error_msg = "Sorry, an error occurred. Please try again."
        elif session['language'] == 'sw':
            error_msg = "Samahani, kuna hitilafu imetokea. Tafadhali jaribu tena."
        elif session['language'] == 'fr':
            error_msg = "Désolé, une erreur s'est produite. Veuillez réessayer."
        elif session['language'] == 'om':
            error_msg = "Dhiifama, dogoggora uumame. Maaloo irra deebi'ii yaali."
        elif session['language'] == 'so':
            error_msg = "Waan xumaatay, khalad ayaa dhacay. Fadlan isku day mar kale."
        elif session['language'] == 'am':
            error_msg = "ይቅርታ፣ ስህተት ተከስቷል። እባክዎ እንደገና ይሞክሩ።"
        else:
            error_msg = "Sorry, an error occurred. Please try again."
            
        return respond(error_msg)

def show_main_menu(session):
    """Display the main menu based on user's language and registration status"""
    patient = Patient.get_by_phone(session['phone_number'])
    
    if patient:
        # User is registered, show main menu
        if session['language'] == 'en':
            response = f"Welcome back, {patient.name}\n"
            response += "1. Report symptoms\n"
            response += "2. Schedule appointment\n"
            response += "3. Messages\n"
            response += "4. Health information\n"
            response += "5. My profile\n"
            response += "0. Back to language selection"
        elif session['language'] == 'sw':
            response = f"Karibu tena, {patient.name}\n"
            response += "1. Ripoti dalili\n"
            response += "2. Panga miadi\n"
            response += "3. Ujumbe\n"
            response += "4. Habari za afya\n"
            response += "5. Wasifu wangu\n"
            response += "0. Rudi kwa uchaguzi wa lugha"
        elif session['language'] == 'fr':
            response = f"Bon retour, {patient.name}\n"
            response += "1. Signaler des symptômes\n"
            response += "2. Planifier un rendez-vous\n"
            response += "3. Messages\n"
            response += "4. Informations de santé\n"
            response += "5. Mon profil\n"
            response += "0. Retour à la sélection de langue"
        elif session['language'] == 'om':
            response = f"Baga nagaan dhufte, {patient.name}\n"
            response += "1. Mallattoo gabaasi\n"
            response += "2. Qabsoo walhitti dhufeenyaa karoorsii\n"
            response += "3. Ergaawwan\n"
            response += "4. Odeeffannoo fayyaa\n"
            response += "5. Profaayilii koo\n"
            response += "0. Gara filannoo afaaniitti deebi'i"
        elif session['language'] == 'so':
            response = f"Ku soo dhawow, {patient.name}\n"
            response += "1. Warbixin calaamadaha\n"
            response += "2. Jadwalka ballanta\n"
            response += "3. Fariimaha\n"
            response += "4. Macluumaadka caafimaadka\n"
            response += "5. Astaantayda\n"
            response += "0. Ku noqo xulashada luuqadda"
        elif session['language'] == 'am':
            response = f"እንደገና እንኳን ደህና መጡ, {patient.name}\n"
            response += "1. የህመም ምልክቶችን ሪፖርት ያድርጉ\n"
            response += "2. ቀጠሮ ያስይዙ\n"
            response += "3. መልዕክቶች\n"
            response += "4. የጤና መረጃ\n"
            response += "5. የግል መገለጫዬ\n"
            response += "0. ወደ ቋንቋ ምርጫ ይመለሱ"
        else:
            # Default to English if language code not recognized
            response = f"Welcome back, {patient.name}\n"
            response += "1. Report symptoms\n"
            response += "2. Schedule appointment\n"
            response += "3. Messages\n"
            response += "4. Health information\n"
            response += "5. My profile\n"
            response += "0. Back to language selection"
    else:
        # User is not registered, prompt for registration
        if session['language'] == 'en':
            response = "Welcome to Tujali Telehealth\n"
            response += "1. Register\n"
            response += "2. Health information\n"
            response += "0. Back to language selection"
        elif session['language'] == 'sw':
            response = "Karibu kwenye Tujali Telehealth\n"
            response += "1. Jisajili\n"
            response += "2. Habari za afya\n"
            response += "0. Rudi kwa uchaguzi wa lugha"
        elif session['language'] == 'fr':
            response = "Bienvenue sur Tujali Telehealth\n"
            response += "1. S'inscrire\n"
            response += "2. Informations de santé\n"
            response += "0. Retour à la sélection de langue"
        elif session['language'] == 'om':
            response = "Tujali Telehealth dhuferra baga nagaan dhufte\n"
            response += "1. Galmaa'i\n"
            response += "2. Odeeffannoo fayyaa\n"
            response += "0. Gara filannoo afaaniitti deebi'i"
        elif session['language'] == 'so':
            response = "Ku soo dhawow Tujali Telehealth\n"
            response += "1. Isdiiwaangeli\n"
            response += "2. Macluumaadka caafimaadka\n"
            response += "0. Ku noqo xulashada luuqadda"
        elif session['language'] == 'am':
            response = "ወደ ቱጃሊ ቴሌሄልዝ እንኳን ደህና መጡ\n"
            response += "1. ይመዝገቡ\n"
            response += "2. የጤና መረጃ\n"
            response += "0. ወደ ቋንቋ ምርጫ ይመለሱ"
        else:
            # Default to English if language code not recognized
            response = "Welcome to Tujali Telehealth\n"
            response += "1. Register\n"
            response += "2. Health information\n"
            response += "0. Back to language selection"
    
    session['state'] = 'main_menu'
    return respond(response)

def handle_main_menu(session, selection):
    """Process main menu selection"""
    patient = Patient.get_by_phone(session['phone_number'])
    
    if patient:
        # Registered user menu options
        if selection == '1':
            return start_symptoms_report(session)
        elif selection == '2':
            return start_appointment_scheduling(session)
        elif selection == '3':
            return show_messages(session)
        elif selection == '4':
            return show_health_info_menu(session)
        elif selection == '5':
            return show_profile(session, patient)
        elif selection == '0':
            session['state'] = 'start'
            return ussd_callback(session['session_id'], '', session['phone_number'], '')
        else:
            return respond(get_invalid_option_text(session))
    else:
        # Unregistered user menu options
        if selection == '1':
            return start_registration(session)
        elif selection == '2':
            return show_health_info_menu(session)
        elif selection == '0':
            session['state'] = 'start'
            return ussd_callback(session['session_id'], '', session['phone_number'], '')
        else:
            return respond(get_invalid_option_text(session))

def start_registration(session):
    """Begin patient registration process"""
    if session['language'] == 'en':
        response = "Please enter your full name:"
    elif session['language'] == 'sw':
        response = "Tafadhali ingiza jina lako kamili:"
    elif session['language'] == 'fr':
        response = "Veuillez entrer votre nom complet:"
    elif session['language'] == 'om':
        response = "Maaloo maqaa guutuu keessan galchaa:"
    elif session['language'] == 'so':
        response = "Fadlan geli magacaaga oo buuxa:"
    elif session['language'] == 'am':
        response = "እባክዎ ሙሉ ስምዎን ያስገቡ:"
    else:
        response = "Please enter your full name:"
    
    session['state'] = 'register_name'
    return respond(response)

def handle_registration(session, input_text):
    """Process registration steps"""
    state = session['state']
    
    if state == 'register_name':
        session['data']['name'] = input_text
        if session['language'] == 'en':
            response = "Enter your age:"
        else:
            response = "Ingiza umri wako:"
        session['state'] = 'register_age'
        return respond(response)
    
    elif state == 'register_age':
        try:
            age = int(input_text)
            session['data']['age'] = age
            if session['language'] == 'en':
                response = "Select your gender:\n"
                response += "1. Male\n"
                response += "2. Female\n"
                response += "3. Other"
            else:
                response = "Chagua jinsia yako:\n"
                response += "1. Mume\n"
                response += "2. Mke\n"
                response += "3. Nyingine"
            session['state'] = 'register_gender'
            return respond(response)
        except ValueError:
            if session['language'] == 'en':
                return respond("Please enter a valid age (numbers only).")
            else:
                return respond("Tafadhali ingiza umri halali (namba tu).")
    
    elif state == 'register_gender':
        if input_text == '1':
            session['data']['gender'] = 'Male'
        elif input_text == '2':
            session['data']['gender'] = 'Female'
        elif input_text == '3':
            session['data']['gender'] = 'Other'
        else:
            return respond(get_invalid_option_text(session))
        
        if session['language'] == 'en':
            response = "Enter your location (county/city):"
        else:
            response = "Ingiza eneo lako (kaunti/mji):"
        session['state'] = 'register_location'
        return respond(response)
    
    elif state == 'register_location':
        session['data']['location'] = input_text
        
        # Ask if the user wants to provide coordinates for location-based provider matching
        if session['language'] == 'en':
            response = "Would you like to provide your location coordinates for better provider matching?\n"
            response += "1. Yes\n"
            response += "2. No, complete registration without coordinates"
        elif session['language'] == 'sw':
            response = "Je, ungependa kutoa mahali pa eneo lako kwa uwianishaji bora wa mtoa huduma?\n"
            response += "1. Ndio\n"
            response += "2. Hapana, kamilisha usajili bila mahali"
        elif session['language'] == 'fr':
            response = "Souhaitez-vous fournir vos coordonnées de localisation pour une meilleure correspondance avec les prestataires?\n"
            response += "1. Oui\n"
            response += "2. Non, terminer l'inscription sans coordonnées"
        else:
            response = "Would you like to provide your location coordinates for better provider matching?\n"
            response += "1. Yes\n"
            response += "2. No, complete registration without coordinates"
        
        session['state'] = 'register_coordinates_choice'
        return respond(response)
        
    elif state == 'register_coordinates_choice':
        if input_text == '1':
            # User wants to provide coordinates
            if session['language'] == 'en':
                response = "Please enter your latitude and longitude separated by a comma (e.g., -1.2921,36.8219):"
            elif session['language'] == 'sw':
                response = "Tafadhali ingiza latitudo na longitudo iliyotenganishwa kwa koma (mfano, -1.2921,36.8219):"
            elif session['language'] == 'fr':
                response = "Veuillez entrer votre latitude et longitude séparées par une virgule (exemple, -1.2921,36.8219):"
            else:
                response = "Please enter your latitude and longitude separated by a comma (e.g., -1.2921,36.8219):"
            
            session['state'] = 'register_coordinates'
            return respond(response)
        elif input_text == '2':
            # Complete registration without coordinates
            patient = Patient.create(
                phone_number=session['phone_number'],
                name=session['data']['name'],
                age=session['data']['age'],
                gender=session['data']['gender'],
                location=session['data']['location'],
                language=session['language']
            )
            
            # Show confirmation
            if session['language'] == 'en':
                response = f"Registration successful!\n"
                response += f"Name: {patient.name}\n"
                response += f"ID: {patient.id}\n"
                response += "Select 0 to continue to main menu."
            else:
                response = f"Usajili umefaulu!\n"
                response += f"Jina: {patient.name}\n"
                response += f"Kitambulisho: {patient.id}\n"
                response += "Chagua 0 kuendelea kwenye menyu kuu."
            
            session['state'] = 'registration_complete'
            return respond(response)
        else:
            return respond(get_invalid_option_text(session))
            
    elif state == 'register_coordinates':
        try:
            # Parse latitude and longitude from input
            coords = input_text.strip().split(',')
            if len(coords) != 2:
                raise ValueError("Invalid format")
                
            latitude = float(coords[0].strip())
            longitude = float(coords[1].strip())
            
            # Validate latitude and longitude ranges
            if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
                raise ValueError("Coordinates out of range")
                
            # Create patient record with coordinates
            patient = Patient.create(
                phone_number=session['phone_number'],
                name=session['data']['name'],
                age=session['data']['age'],
                gender=session['data']['gender'],
                location=session['data']['location'],
                language=session['language'],
                coordinates=(latitude, longitude)
            )
            
            # Show confirmation
            if session['language'] == 'en':
                response = f"Registration successful!\n"
                response += f"Name: {patient.name}\n"
                response += f"Location: {patient.location}\n"
                response += f"Coordinates saved for location-based provider matching.\n"
                response += f"ID: {patient.id}\n"
                response += "Select 0 to continue to main menu."
            elif session['language'] == 'sw':
                response = f"Usajili umefaulu!\n"
                response += f"Jina: {patient.name}\n"
                response += f"Eneo: {patient.location}\n"
                response += f"Mahali pamehifadhiwa kwa uwianishaji wa mtoa huduma kulingana na eneo.\n"
                response += f"Kitambulisho: {patient.id}\n"
                response += "Chagua 0 kuendelea kwenye menyu kuu."
            elif session['language'] == 'fr':
                response = f"Inscription réussie!\n"
                response += f"Nom: {patient.name}\n"
                response += f"Emplacement: {patient.location}\n"
                response += f"Coordonnées enregistrées pour la correspondance des prestataires basée sur la localisation.\n"
                response += f"ID: {patient.id}\n"
                response += "Sélectionnez 0 pour continuer vers le menu principal."
            else:
                response = f"Registration successful!\n"
                response += f"Name: {patient.name}\n"
                response += f"Location: {patient.location}\n"
                response += f"Coordinates saved for location-based provider matching.\n"
                response += f"ID: {patient.id}\n"
                response += "Select 0 to continue to main menu."
            
            session['state'] = 'registration_complete'
            return respond(response)
        except ValueError as e:
            # Invalid coordinate format
            if session['language'] == 'en':
                response = "Invalid coordinates format. Please enter latitude and longitude separated by a comma (e.g., -1.2921,36.8219).\n"
                response += "Try again or press 0 to cancel and complete registration without coordinates."
            elif session['language'] == 'sw':
                response = "Umbali si sahihi. Tafadhali ingiza latitudo na longitudo iliyotenganishwa kwa koma (mfano, -1.2921,36.8219).\n"
                response += "Jaribu tena au bonyeza 0 kughairi na kukamilisha usajili bila mahali."
            elif session['language'] == 'fr':
                response = "Format de coordonnées invalide. Veuillez entrer la latitude et la longitude séparées par une virgule (exemple, -1.2921,36.8219).\n"
                response += "Réessayez ou appuyez sur 0 pour annuler et terminer l'inscription sans coordonnées."
            else:
                response = "Invalid coordinates format. Please enter latitude and longitude separated by a comma (e.g., -1.2921,36.8219).\n"
                response += "Try again or press 0 to cancel and complete registration without coordinates."
            
            if input_text == '0':
                # Create patient record without coordinates
                patient = Patient.create(
                    phone_number=session['phone_number'],
                    name=session['data']['name'],
                    age=session['data']['age'],
                    gender=session['data']['gender'],
                    location=session['data']['location'],
                    language=session['language']
                )
                
                # Show confirmation
                if session['language'] == 'en':
                    response = f"Registration successful!\n"
                    response += f"Name: {patient.name}\n"
                    response += f"ID: {patient.id}\n"
                    response += "Select 0 to continue to main menu."
                else:
                    response = f"Usajili umefaulu!\n"
                    response += f"Jina: {patient.name}\n"
                    response += f"Kitambulisho: {patient.id}\n"
                    response += "Chagua 0 kuendelea kwenye menyu kuu."
                
                session['state'] = 'registration_complete'
                return respond(response)
            else:
                return respond(response)
    
    elif state == 'registration_complete':
        if input_text == '0':
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    else:
        # Unknown registration state, return to main menu
        return show_main_menu(session)

def start_symptoms_report(session):
    """Begin symptom reporting process"""
    if session['language'] == 'en':
        response = "Please describe your symptoms:"
    else:
        response = "Tafadhali eleza dalili zako:"
    
    session['state'] = 'symptom_description'
    return respond(response)

def handle_symptoms(session, input_text):
    """Process symptom reporting steps"""
    state = session['state']
    patient = Patient.get_by_phone(session['phone_number'])
    
    if state == 'symptom_description':
        session['data']['symptoms'] = input_text
        patient.add_symptom(input_text)
        
        # Ask about symptom duration
        if session['language'] == 'en':
            response = "How long have you had these symptoms?\n"
            response += "1. Today only\n"
            response += "2. Few days\n"
            response += "3. A week or more\n"
            response += "4. A month or more"
        else:
            response = "Umepatwa na dalili hizi kwa muda gani?\n"
            response += "1. Leo tu\n"
            response += "2. Siku chache\n"
            response += "3. Wiki moja au zaidi\n"
            response += "4. Mwezi mmoja au zaidi"
        
        session['state'] = 'symptom_duration'
        return respond(response)
    
    elif state == 'symptom_duration':
        if input_text in ['1', '2', '3', '4']:
            durations = {
                '1': 'Today only',
                '2': 'Few days',
                '3': 'A week or more',
                '4': 'A month or more'
            }
            session['data']['duration'] = durations[input_text]
            
            # Ask about symptom severity
            if session['language'] == 'en':
                response = "How severe are your symptoms?\n"
                response += "1. Mild - I can function normally\n"
                response += "2. Moderate - Affecting daily activities\n"
                response += "3. Severe - Cannot function normally"
            else:
                response = "Dalili zako ni kali kiasi gani?\n"
                response += "1. Kidogo - Ninaweza kufanya kazi kama kawaida\n"
                response += "2. Wastani - Zinaathiri shughuli za kila siku\n"
                response += "3. Kali - Siwezi kufanya kazi kama kawaida"
            
            session['state'] = 'symptom_severity'
            return respond(response)
        else:
            return respond(get_invalid_option_text(session))
    
    elif state == 'symptom_severity':
        if input_text in ['1', '2', '3']:
            severities = {
                '1': 'Mild',
                '2': 'Moderate',
                '3': 'Severe'
            }
            session['data']['severity'] = severities[input_text]
            
            # Record the symptom with enhanced metadata
            symptom_text = session['data']['symptoms']
            symptom_severity = session['data']['severity']
            symptom_duration = session['data']['duration']
            
            # Update the symptom text to include duration for better categorization
            enhanced_symptom_text = f"{symptom_text} for {symptom_duration}"
            
            # Add the symptom to patient record with severity
            patient.add_symptom(enhanced_symptom_text, severity=symptom_severity)
            
            # Find an available provider
            provider = Provider.get_all()[0]  # For simplicity, get the first provider
            
            # Create a message for the provider with symptom details
            message_content = f"Symptoms: {symptom_text}\n"
            message_content += f"Duration: {symptom_duration}\n"
            message_content += f"Severity: {symptom_severity}"
            
            Message.create(
                provider_id=provider.id,
                patient_id=patient.id,
                content=message_content,
                sender_type='patient'
            )
            
            # Show confirmation and next steps
            if session['language'] == 'en':
                response = "Thank you for reporting your symptoms.\n"
                response += "A healthcare provider will review your symptoms and respond shortly.\n"
                response += "1. Schedule an appointment\n"
                response += "0. Return to main menu"
            else:
                response = "Asante kwa kuripoti dalili zako.\n"
                response += "Mtoa huduma ya afya atakagua dalili zako na kujibu hivi karibuni.\n"
                response += "1. Panga miadi\n"
                response += "0. Rudi kwenye menyu kuu"
            
            session['state'] = 'symptom_next_steps'
            return respond(response)
        else:
            return respond(get_invalid_option_text(session))
    
    elif state == 'symptom_next_steps':
        if input_text == '1':
            return start_appointment_scheduling(session)
        elif input_text == '0':
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    else:
        # Unknown symptom state, return to main menu
        return show_main_menu(session)

def start_appointment_scheduling(session):
    """Begin appointment scheduling process"""
    # Get available dates (next 7 days)
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime('%d-%m-%Y') for i in range(1, 8)]
    
    session['data']['available_dates'] = dates
    
    if session['language'] == 'en':
        response = "Select preferred date:\n"
    else:
        response = "Chagua tarehe unayopendelea:\n"
    
    # Show dates
    for i, date in enumerate(dates, 1):
        # Format the date in a user-friendly way
        formatted_date = utils.format_date(date, session['language'])
        response += f"{i}. {formatted_date}\n"
    
    session['state'] = 'appointment_date'
    return respond(response)

def handle_appointments(session, input_text):
    """Process appointment scheduling steps"""
    state = session['state']
    patient = Patient.get_by_phone(session['phone_number'])
    
    if state == 'appointment_date':
        try:
            selection = int(input_text)
            if 1 <= selection <= len(session['data']['available_dates']):
                selected_date = session['data']['available_dates'][selection - 1]
                session['data']['selected_date'] = selected_date
                
                # Get available time slots
                time_slots = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
                session['data']['available_times'] = time_slots
                
                if session['language'] == 'en':
                    response = "Select preferred time:\n"
                else:
                    response = "Chagua wakati unaopendelea:\n"
                
                # Show time slots
                for i, time in enumerate(time_slots, 1):
                    response += f"{i}. {time}\n"
                
                session['state'] = 'appointment_time'
                return respond(response)
            else:
                return respond(get_invalid_option_text(session))
        except ValueError:
            return respond(get_invalid_option_text(session))
    
    elif state == 'appointment_time':
        try:
            selection = int(input_text)
            if 1 <= selection <= len(session['data']['available_times']):
                selected_time = session['data']['available_times'][selection - 1]
                session['data']['selected_time'] = selected_time
                
                # Get patient object
                patient = Patient.get_by_phone(session['phone_number'])
                
                # Find nearby providers if patient has location data
                if patient.coordinates:
                    providers = patient.find_nearby_providers(max_distance=50)
                    session['data']['using_location'] = True
                else:
                    providers = Provider.get_all()
                    session['data']['using_location'] = False
                
                session['data']['available_providers'] = providers
                
                if session['language'] == 'en':
                    if patient.coordinates:
                        response = "Select healthcare provider (sorted by distance):\n"
                    else:
                        response = "Select healthcare provider:\n"
                elif session['language'] == 'sw':
                    if patient.coordinates:
                        response = "Chagua mtoa huduma ya afya (imepangwa kwa umbali):\n"
                    else:
                        response = "Chagua mtoa huduma ya afya:\n"
                elif session['language'] == 'fr':
                    if patient.coordinates:
                        response = "Sélectionnez un prestataire de soins de santé (classé par distance):\n"
                    else:
                        response = "Sélectionnez un prestataire de soins de santé:\n"
                else:
                    if patient.coordinates:
                        response = "Select healthcare provider (sorted by distance):\n"
                    else: 
                        response = "Select healthcare provider:\n"
                
                # Show providers with distance information if available
                for i, provider in enumerate(providers, 1):
                    if hasattr(provider, 'distance') and provider.distance is not None:
                        # Show distance to provider rounded to one decimal place
                        distance_km = round(provider.distance, 1)
                        response += f"{i}. {provider.name} ({provider.specialization}) - {distance_km} km\n"
                    else:
                        response += f"{i}. {provider.name} ({provider.specialization})\n"
                
                session['state'] = 'appointment_provider'
                return respond(response)
            else:
                return respond(get_invalid_option_text(session))
        except ValueError:
            return respond(get_invalid_option_text(session))
    
    elif state == 'appointment_provider':
        try:
            selection = int(input_text)
            if 1 <= selection <= len(session['data']['available_providers']):
                selected_provider = session['data']['available_providers'][selection - 1]
                
                # Create appointment
                appointment = Appointment.create(
                    patient_id=patient.id,
                    provider_id=selected_provider.id,
                    date=session['data']['selected_date'],
                    time=session['data']['selected_time']
                )
                
                # Show confirmation
                formatted_date = utils.format_date(
                    session['data']['selected_date'], 
                    session['language']
                )
                
                if session['language'] == 'en':
                    response = "Appointment scheduled successfully!\n"
                    response += f"Date: {formatted_date}\n"
                    response += f"Time: {session['data']['selected_time']}\n"
                    response += f"Provider: {selected_provider.name}\n"
                    response += f"Appointment ID: {appointment.id}\n"
                    response += "0. Return to main menu"
                else:
                    response = "Miadi imepangwa kwa mafanikio!\n"
                    response += f"Tarehe: {formatted_date}\n"
                    response += f"Wakati: {session['data']['selected_time']}\n"
                    response += f"Mtoa huduma: {selected_provider.name}\n"
                    response += f"Kitambulisho cha miadi: {appointment.id}\n"
                    response += "0. Rudi kwenye menyu kuu"
                
                session['state'] = 'appointment_complete'
                return respond(response)
            else:
                return respond(get_invalid_option_text(session))
        except ValueError:
            return respond(get_invalid_option_text(session))
    
    elif state == 'appointment_complete':
        if input_text == '0':
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    else:
        # Unknown appointment state, return to main menu
        return show_main_menu(session)

def show_messages(session):
    """Show messages for the patient"""
    patient = Patient.get_by_phone(session['phone_number'])
    provider = Provider.get_all()[0]  # For simplicity, get the first provider
    
    # Get conversation
    messages = Message.get_conversation(provider.id, patient.id)
    
    if messages:
        # Show the last few messages
        recent_messages = messages[-3:] if len(messages) > 3 else messages
        
        if session['language'] == 'en':
            response = "Recent messages:\n"
            for i, msg in enumerate(recent_messages, 1):
                sender = "You" if msg.sender_type == 'patient' else "Doctor"
                response += f"{i}. {sender}: {msg.content[:30]}...\n"
            
            response += "\n1. Send new message\n"
            response += "0. Return to main menu"
        else:
            response = "Ujumbe wa hivi karibuni:\n"
            for i, msg in enumerate(recent_messages, 1):
                sender = "Wewe" if msg.sender_type == 'patient' else "Daktari"
                response += f"{i}. {sender}: {msg.content[:30]}...\n"
            
            response += "\n1. Tuma ujumbe mpya\n"
            response += "0. Rudi kwenye menyu kuu"
    else:
        if session['language'] == 'en':
            response = "You have no messages yet.\n"
            response += "1. Send new message\n"
            response += "0. Return to main menu"
        else:
            response = "Bado huna ujumbe.\n"
            response += "1. Tuma ujumbe mpya\n"
            response += "0. Rudi kwenye menyu kuu"
    
    session['state'] = 'message_menu'
    return respond(response)

def handle_messages(session, input_text):
    """Process messaging steps"""
    state = session['state']
    patient = Patient.get_by_phone(session['phone_number'])
    provider = Provider.get_all()[0]  # For simplicity, get the first provider
    
    if state == 'message_menu':
        if input_text == '1':
            if session['language'] == 'en':
                response = "Type your message:"
            else:
                response = "Andika ujumbe wako:"
            
            session['state'] = 'message_compose'
            return respond(response)
        elif input_text == '0':
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    elif state == 'message_compose':
        # Create message
        Message.create(
            provider_id=provider.id,
            patient_id=patient.id,
            content=input_text,
            sender_type='patient'
        )
        
        if session['language'] == 'en':
            response = "Message sent successfully.\n"
            response += "The healthcare provider will respond soon.\n"
            response += "0. Return to main menu"
        else:
            response = "Ujumbe umetumwa kwa mafanikio.\n"
            response += "Mtoa huduma ya afya atajibu hivi karibuni.\n"
            response += "0. Rudi kwenye menyu kuu"
        
        session['state'] = 'message_sent'
        return respond(response)
    
    elif state == 'message_sent':
        if input_text == '0':
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    elif state == 'profile_view':
        patient = Patient.get_by_phone(session['phone_number'])
        
        if input_text == '1':
            # Update location coordinates option selected
            if session['language'] == 'en':
                response = "To update your location coordinates, please enter latitude and longitude separated by a comma (e.g., -1.2921,36.8219):"
            elif session['language'] == 'sw':
                response = "Kusasisha mahali pako, tafadhali ingiza latitudo na longitudo iliyotenganishwa kwa koma (mfano, -1.2921,36.8219):"
            elif session['language'] == 'fr':
                response = "Pour mettre à jour vos coordonnées de localisation, veuillez entrer la latitude et la longitude séparées par une virgule (exemple, -1.2921,36.8219):"
            else:
                response = "To update your location coordinates, please enter latitude and longitude separated by a comma (e.g., -1.2921,36.8219):"
            
            session['state'] = 'update_coordinates'
            return respond(response)
        elif input_text == '0':
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    elif state == 'update_coordinates':
        try:
            # Parse latitude and longitude from input
            coords = input_text.strip().split(',')
            if len(coords) != 2:
                raise ValueError("Invalid format")
                
            latitude = float(coords[0].strip())
            longitude = float(coords[1].strip())
            
            # Validate latitude and longitude ranges
            if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
                raise ValueError("Coordinates out of range")
                
            patient = Patient.get_by_phone(session['phone_number'])
            patient.update_coordinates(latitude, longitude)
            
            if session['language'] == 'en':
                response = "Location coordinates updated successfully!\n"
                response += "You will now receive location-based provider recommendations.\n"
                response += "0. Return to main menu"
            elif session['language'] == 'sw':
                response = "Mahali pako pamewekwa kwa mafanikio!\n"
                response += "Sasa utapata mapendekezo ya watoa huduma kulingana na eneo lako.\n"
                response += "0. Rudi kwenye menyu kuu"
            elif session['language'] == 'fr':
                response = "Coordonnées de localisation mises à jour avec succès!\n"
                response += "Vous recevrez désormais des recommandations de prestataires basées sur la localisation.\n"
                response += "0. Retour au menu principal"
            else:
                response = "Location coordinates updated successfully!\n"
                response += "You will now receive location-based provider recommendations.\n"
                response += "0. Return to main menu"
            
            session['state'] = 'coordinates_updated'
            return respond(response)
        except ValueError as e:
            # Invalid coordinate format
            if session['language'] == 'en':
                response = "Invalid coordinates format. Please enter latitude and longitude separated by a comma (e.g., -1.2921,36.8219).\n"
                response += "Try again or press 0 to cancel."
            elif session['language'] == 'sw':
                response = "Umbali si sahihi. Tafadhali ingiza latitudo na longitudo iliyotenganishwa kwa koma (mfano, -1.2921,36.8219).\n"
                response += "Jaribu tena au bonyeza 0 kughairi."
            elif session['language'] == 'fr':
                response = "Format de coordonnées invalide. Veuillez entrer la latitude et la longitude séparées par une virgule (exemple, -1.2921,36.8219).\n"
                response += "Réessayez ou appuyez sur 0 pour annuler."
            else:
                response = "Invalid coordinates format. Please enter latitude and longitude separated by a comma (e.g., -1.2921,36.8219).\n"
                response += "Try again or press 0 to cancel."
            
            if input_text == '0':
                return show_main_menu(session)
            else:
                return respond(response)
    
    elif state == 'coordinates_updated':
        if input_text == '0':
            return show_main_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    else:
        # Unknown message state, return to main menu
        return show_main_menu(session)

def show_health_info_menu(session):
    """Show health information menu"""
    if session['language'] == 'en':
        response = "Health Information:\n"
        response += "1. COVID-19 Information\n"
        response += "2. Maternal Health\n"
        response += "3. Chronic Diseases\n"
        response += "4. First Aid\n"
        response += "0. Return to main menu"
    else:
        response = "Habari za Afya:\n"
        response += "1. Habari za COVID-19\n"
        response += "2. Afya ya Uzazi\n"
        response += "3. Magonjwa ya Muda Mrefu\n"
        response += "4. Huduma ya Kwanza\n"
        response += "0. Rudi kwenye menyu kuu"
    
    session['state'] = 'info_menu'
    return respond(response)

def handle_health_info(session, input_text):
    """Process health information selection"""
    state = session['state']
    
    if state == 'info_menu':
        if input_text == '0':
            return show_main_menu(session)
        
        topics = {
            '1': 'covid',
            '2': 'maternal',
            '3': 'chronic',
            '4': 'firstaid'
        }
        
        if input_text in topics:
            topic = topics[input_text]
            session['data']['selected_topic'] = topic
            
            # Get health info from database based on language and topic
            health_info_list = HealthInfo.get_by_language(session['language'])
            
            # In a real application, you'd filter by topic as well
            if health_info_list:
                info = health_info_list[0]  # Just get the first one for demo
                
                if session['language'] == 'en':
                    response = f"{info.title}:\n"
                    response += f"{info.content}\n\n"
                    response += "0. Return to health information menu"
                else:
                    response = f"{info.title}:\n"
                    response += f"{info.content}\n\n"
                    response += "0. Rudi kwenye menyu ya habari za afya"
            else:
                if session['language'] == 'en':
                    response = "Information not available at this time.\n"
                    response += "0. Return to health information menu"
                else:
                    response = "Habari haipatikani kwa sasa.\n"
                    response += "0. Rudi kwenye menyu ya habari za afya"
            
            session['state'] = 'info_detail'
            return respond(response)
        else:
            return respond(get_invalid_option_text(session))
    
    elif state == 'info_detail':
        if input_text == '0':
            return show_health_info_menu(session)
        else:
            return respond(get_invalid_option_text(session))
    
    else:
        # Unknown info state, return to main menu
        return show_main_menu(session)

def show_profile(session, patient):
    """Show patient profile"""
    has_coordinates = patient.coordinates is not None
    
    if session['language'] == 'en':
        response = f"Your Profile:\n"
        response += f"Name: {patient.name}\n"
        response += f"Age: {patient.age}\n"
        response += f"Gender: {patient.gender}\n"
        response += f"Location: {patient.location}\n"
        
        # Show coordinates if available
        if has_coordinates:
            response += f"GPS Location: Available\n"
        else:
            response += f"GPS Location: Not set\n"
            
        response += f"ID: {patient.id}\n\n"
        response += "1. Update location coordinates\n"
        response += "0. Return to main menu"
    elif session['language'] == 'sw':
        response = f"Wasifu Wako:\n"
        response += f"Jina: {patient.name}\n"
        response += f"Umri: {patient.age}\n"
        response += f"Jinsia: {patient.gender}\n"
        response += f"Eneo: {patient.location}\n"
        
        # Show coordinates if available
        if has_coordinates:
            response += f"Eneo la GPS: Linapatikana\n"
        else:
            response += f"Eneo la GPS: Halijawekwa\n"
            
        response += f"Kitambulisho: {patient.id}\n\n"
        response += "1. Sasisha mahali pa eneo\n"
        response += "0. Rudi kwenye menyu kuu"
    elif session['language'] == 'fr':
        response = f"Votre Profil:\n"
        response += f"Nom: {patient.name}\n"
        response += f"Âge: {patient.age}\n"
        response += f"Sexe: {patient.gender}\n"
        response += f"Emplacement: {patient.location}\n"
        
        # Show coordinates if available
        if has_coordinates:
            response += f"Localisation GPS: Disponible\n"
        else:
            response += f"Localisation GPS: Non définie\n"
            
        response += f"ID: {patient.id}\n\n"
        response += "1. Mettre à jour les coordonnées de localisation\n"
        response += "0. Retour au menu principal"
    else:
        response = f"Your Profile:\n"
        response += f"Name: {patient.name}\n"
        response += f"Age: {patient.age}\n"
        response += f"Gender: {patient.gender}\n"
        response += f"Location: {patient.location}\n"
        
        # Show coordinates if available
        if has_coordinates:
            response += f"GPS Location: Available\n"
        else:
            response += f"GPS Location: Not set\n"
            
        response += f"ID: {patient.id}\n\n"
        response += "1. Update location coordinates\n"
        response += "0. Return to main menu"
    
    session['state'] = 'profile_view'
    return respond(response)

def get_invalid_option_text(session):
    """Get invalid option text based on language"""
    if session['language'] == 'en':
        return "Invalid option. Please try again."
    elif session['language'] == 'sw':
        return "Chaguo batili. Tafadhali jaribu tena."
    elif session['language'] == 'fr':
        return "Option invalide. Veuillez réessayer."
    elif session['language'] == 'om':
        return "Filannoon sirrii miti. Maaloo irra deebi'ii yaali."
    elif session['language'] == 'so':
        return "Doorasho aan shaqeyneyn. Fadlan mar kale isku day."
    elif session['language'] == 'am':
        return "ልክ ያልሆነ ምርጫ። እባክዎ እንደገና ይሞክሩ።"
    else:
        return "Invalid option. Please try again."

def respond(text):
    """Format USSD response with appropriate prefix"""
    # Africa's Talking expects responses to be prefixed
    # CON: Expects more input
    # END: End of session
    
    # Check for specific end conditions
    end_conditions = [
        "successful", "thank you", "asante", "finished", "completed", 
        "error occurred", "hitilafu", "umekamilika", "umefaulu"
    ]
    
    # Most USSD responses should expect more input
    # Only end the session for specific end conditions
    if any(condition in text.lower() for condition in end_conditions) and not any(prompt in text.lower() for prompt in ["select", "enter", "choose", "chagua", "ingiza"]):
        # End session only when we're done and not asking for more input
        prefix = "END "
    else:
        # Continue the session for navigation, input prompts, and menu displays
        prefix = "CON "
    
    return prefix + text
