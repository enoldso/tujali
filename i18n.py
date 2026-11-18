"""USSD and SMS text in English and Kiswahili.

Keep screens short: most networks cut USSD screens at ~182 characters.
"""

STRINGS = {
    # --- general ---
    'welcome': {
        'en': 'Welcome to Tujali - specialist care on any phone.\nKaribu Tujali.\n1. English\n2. Kiswahili',
        'sw': 'Welcome to Tujali - specialist care on any phone.\nKaribu Tujali.\n1. English\n2. Kiswahili',
    },
    'invalid': {'en': 'Invalid choice. Try again.', 'sw': 'Chaguo si sahihi. Jaribu tena.'},
    'back': {'en': '0. Back', 'sw': '0. Rudi'},
    'more': {'en': '9. More', 'sw': '9. Zaidi'},
    'main_menu_hint': {'en': '00. Main menu', 'sw': '00. Menyu kuu'},
    'error': {'en': 'Sorry, something went wrong. Please dial again.',
              'sw': 'Samahani, kuna hitilafu. Tafadhali piga tena.'},
    'goodbye': {'en': 'Thank you for using Tujali.', 'sw': 'Asante kwa kutumia Tujali.'},

    'main': {
        'en': 'Tujali{greeting}\n1. See a specialist\n2. My appointments\n3. Report illness\n'
              '4. Health alerts\n5. Emergency help\n6. My account',
        'sw': 'Tujali{greeting}\n1. Ona daktari bingwa\n2. Miadi yangu\n3. Ripoti ugonjwa\n'
              '4. Tahadhari za afya\n5. Msaada wa dharura\n6. Akaunti yangu',
    },

    # --- registration ---
    'reg_name': {'en': 'Please register first (once only).\nEnter your full name:',
                 'sw': 'Tafadhali jisajili kwanza (mara moja tu).\nAndika jina lako kamili:'},
    'reg_age': {'en': 'Enter your age in years:', 'sw': 'Andika umri wako (miaka):'},
    'reg_gender': {'en': 'You are:\n1. Female\n2. Male\n3. Prefer not to say',
                   'sw': 'Wewe ni:\n1. Mwanamke\n2. Mwanamume\n3. Sipendi kusema'},
    'pick_region': {'en': 'Choose your region:', 'sw': 'Chagua eneo lako:'},
    'pick_county': {'en': 'Choose your county:', 'sw': 'Chagua kaunti yako:'},
    'registered': {'en': 'Registered. Welcome {name}!', 'sw': 'Umesajiliwa. Karibu {name}!'},

    # --- booking ---
    'bk_specialty': {'en': 'What do you need help with?', 'sw': 'Unahitaji msaada wa nini?'},
    'bk_complaint': {'en': 'Briefly describe the problem\n(e.g. itchy rash for 2 weeks):',
                     'sw': 'Eleza tatizo kwa ufupi\n(mf. upele unaowasha wiki 2):'},
    'bk_mode': {'en': 'How would you like to see the specialist?\n1. Phone call (doctor calls you)\n'
                      '2. Visit in person\n0. Back',
                'sw': 'Ungependa kumwona daktari vipi?\n1. Simu (daktari atakupigia)\n'
                      '2. Kumtembelea\n0. Rudi'},
    'bk_specialist': {'en': 'Choose a specialist:', 'sw': 'Chagua daktari:'},
    'bk_slot': {'en': 'Choose a time:', 'sw': 'Chagua wakati:'},
    'bk_no_slots': {'en': 'No free times this week. Choose another specialist.\n0. Back',
                    'sw': 'Hakuna nafasi wiki hii. Chagua daktari mwingine.\n0. Rudi'},
    'bk_confirm': {'en': 'Confirm:\n{doctor} ({specialty})\n{when}, {mode}\nFee KES {fee}\n1. Confirm\n2. Cancel',
                   'sw': 'Thibitisha:\n{doctor} ({specialty})\n{when}, {mode}\nAda KES {fee}\n1. Thibitisha\n2. Ghairi'},
    'mode_phone': {'en': 'phone call', 'sw': 'kwa simu'},
    'mode_in_person': {'en': 'in person', 'sw': 'ana kwa ana'},
    'bk_taken': {'en': 'Sorry, that time was just taken.', 'sw': 'Samahani, wakati huo umechukuliwa.'},
    'bk_done_phone': {
        'en': 'Booked! Ref {ref}. {doctor} will call you on {when}. Fee KES {fee}. Details sent by SMS.',
        'sw': 'Imethibitishwa! Kumb. {ref}. {doctor} atakupigia {when}. Ada KES {fee}. Maelezo kwa SMS.'},
    'bk_done_visit': {
        'en': 'Booked! Ref {ref}. See {doctor} at {place} on {when}. Fee KES {fee}. Details sent by SMS.',
        'sw': 'Imethibitishwa! Kumb. {ref}. Mwone {doctor} {place} {when}. Ada KES {fee}. Maelezo kwa SMS.'},
    'bk_cancelled': {'en': 'Booking not made. Dial again any time.',
                     'sw': 'Miadi haikufanywa. Piga tena wakati wowote.'},
    'bk_waitlist': {
        'en': 'No {specialty} specialist is free right now. Ref {ref}. We will SMS you as soon as one is available.',
        'sw': 'Hakuna daktari wa {specialty} kwa sasa. Kumb. {ref}. Tutakutumia SMS akipatikana.'},

    # --- appointments ---
    'appts': {'en': 'Your appointments:', 'sw': 'Miadi yako:'},
    'appts_none': {'en': 'You have no appointments.\n1. See a specialist\n0. Back',
                   'sw': 'Huna miadi.\n1. Ona daktari bingwa\n0. Rudi'},
    'appt_booked': {'en': '{ref}\n{doctor} ({specialty})\n{when}, {mode}\n1. Cancel appointment\n0. Back',
                    'sw': '{ref}\n{doctor} ({specialty})\n{when}, {mode}\n1. Ghairi miadi\n0. Rudi'},
    'appt_waitlist': {'en': '{ref}\nWaiting for a {specialty} specialist. We will SMS you.\n1. Cancel request\n0. Back',
                      'sw': '{ref}\nTunasubiri daktari wa {specialty}. Tutakutumia SMS.\n1. Ghairi ombi\n0. Rudi'},
    'appt_advice': {'en': 'Advice from {doctor}:\n{advice}\n1. Send full advice by SMS\n2. Book follow-up\n0. Back',
                    'sw': 'Ushauri wa {doctor}:\n{advice}\n1. Tuma ushauri kwa SMS\n2. Miadi ya kufuatilia\n0. Rudi'},
    'appt_cancel_confirm': {'en': 'Cancel {ref}?\n1. Yes, cancel\n2. No', 'sw': 'Ghairi {ref}?\n1. Ndiyo\n2. Hapana'},
    'appt_cancelled': {'en': 'Appointment {ref} cancelled.', 'sw': 'Miadi {ref} imeghairiwa.'},
    'advice_sent': {'en': 'Advice sent to you by SMS.', 'sw': 'Ushauri umetumwa kwa SMS.'},
    'label_advice': {'en': 'Advice', 'sw': 'Ushauri'},
    'label_waiting': {'en': 'Waiting', 'sw': 'Inasubiri'},

    # --- illness reporting ---
    'sx_group': {'en': 'Report illness. What is the main sign?', 'sw': 'Ripoti ugonjwa. Dalili kuu ni ipi?'},
    'sx_people': {'en': 'How many people at home have it?\n1. One person\n2. 2 or 3 people\n3. 4 or more\n0. Back',
                  'sw': 'Watu wangapi nyumbani wanayo?\n1. Mtu mmoja\n2. Watu 2 au 3\n3. Wanne au zaidi\n0. Rudi'},
    'sx_danger': {'en': 'Any of these? Very weak, fits, fast breathing, blood in vomit or stool, '
                        'unable to drink.\n1. Yes\n2. No',
                  'sw': 'Kuna yoyote? Udhaifu mkubwa, degedege, kupumua haraka, damu kwenye matapishi '
                        'au choo, kushindwa kunywa.\n1. Ndiyo\n2. Hapana'},
    'sx_urgent': {'en': 'Report received. This needs care NOW: go to the nearest health facility '
                        'or call 1199 (Red Cross). Thank you for protecting your community.',
                  'sw': 'Ripoti imepokelewa. Hii inahitaji matibabu SASA: nenda kituo cha afya '
                        'kilicho karibu au piga 1199. Asante kwa kulinda jamii.'},
    'sx_thanks': {'en': 'Report received - thank you. {advice} Need a specialist? Dial again, choose 1.',
                  'sw': 'Ripoti imepokelewa - asante. {advice} Unahitaji daktari? Piga tena, chagua 1.'},

    # --- alerts ---
    'alerts': {'en': 'Health alerts for {county}:', 'sw': 'Tahadhari za afya {county}:'},
    'alerts_none': {'en': 'No alerts for {county} now. Stay safe: wash hands, boil drinking water, '
                          'sleep under a treated net.\n0. Back',
                    'sw': 'Hakuna tahadhari {county} sasa. Jilinde: nawa mikono, chemsha maji ya kunywa, '
                          'lala kwenye chandarua.\n0. Rudi'},

    # --- emergency ---
    'emergency': {'en': 'EMERGENCY - call free:\n{numbers}\nGo to the nearest health facility if you can.',
                  'sw': 'DHARURA - piga bure:\n{numbers}\nNenda kituo cha afya kilicho karibu ukiweza.'},

    # --- account ---
    'account': {'en': 'My account\n1. Change language\n2. Change county\n3. My details\n4. Delete my data\n0. Back',
                'sw': 'Akaunti yangu\n1. Badili lugha\n2. Badili kaunti\n3. Taarifa zangu\n4. Futa taarifa zangu\n0. Rudi'},
    'account_lang': {'en': 'Choose language:\n1. English\n2. Kiswahili', 'sw': 'Chagua lugha:\n1. English\n2. Kiswahili'},
    'account_details': {'en': '{name}, {age} yrs\n{county}\n{phone}\n0. Back',
                        'sw': '{name}, miaka {age}\n{county}\n{phone}\n0. Rudi'},
    'account_updated': {'en': 'Saved.', 'sw': 'Imehifadhiwa.'},
    'account_delete': {'en': 'Delete your profile and cancel upcoming appointments? This cannot be undone.'
                             '\n1. Yes, delete\n2. No',
                       'sw': 'Futa taarifa zako na ughairi miadi ijayo? Haiwezi kurudishwa.\n1. Ndiyo, futa\n2. Hapana'},
    'account_deleted': {'en': 'Your data has been deleted. You can register again any time.',
                        'sw': 'Taarifa zako zimefutwa. Unaweza kujisajili tena wakati wowote.'},

    # --- SMS ---
    'sms_booked_phone': {
        'en': 'Tujali: Booked {ref}. {doctor} ({specialty}) will call you on {when}. Keep your phone on. '
              'Fee KES {fee}. To cancel dial {code} > My appointments.',
        'sw': 'Tujali: Miadi {ref}. {doctor} ({specialty}) atakupigia {when}. Weka simu wazi. '
              'Ada KES {fee}. Kughairi piga {code} > Miadi yangu.'},
    'sms_booked_visit': {
        'en': 'Tujali: Booked {ref}. See {doctor} ({specialty}) at {place} on {when}. Fee KES {fee}. '
              'To cancel dial {code} > My appointments.',
        'sw': 'Tujali: Miadi {ref}. Mwone {doctor} ({specialty}) {place} {when}. Ada KES {fee}. '
              'Kughairi piga {code} > Miadi yangu.'},
    'sms_waitlist': {
        'en': 'Tujali: Request {ref} received. We will SMS you when a {specialty} specialist is available.',
        'sw': 'Tujali: Ombi {ref} limepokelewa. Tutakutumia SMS daktari wa {specialty} akipatikana.'},
    'sms_cancelled': {'en': 'Tujali: Appointment {ref} has been cancelled.',
                      'sw': 'Tujali: Miadi {ref} imeghairiwa.'},
    'sms_cancelled_by_doctor': {
        'en': 'Tujali: Sorry, {doctor} cancelled appointment {ref}. Dial {code} to book another time.',
        'sw': 'Tujali: Samahani, {doctor} ameghairi miadi {ref}. Piga {code} kupanga wakati mwingine.'},
    'sms_advice': {'en': 'Tujali - advice from {doctor} ({ref}): {advice}',
                   'sw': 'Tujali - ushauri wa {doctor} ({ref}): {advice}'},
    'sms_reminder': {'en': 'Tujali reminder: {doctor} will call you today at {time} ({ref}). Keep your phone on.',
                     'sw': 'Tujali kumbusho: {doctor} atakupigia leo saa {time} ({ref}). Weka simu wazi.'},
}

# Self-care advice after an illness report (no danger signs).
SYNDROME_ADVICE = {
    'fever': {'en': 'Get a malaria test at a health facility within 24 hours. Drink plenty of fluids.',
              'sw': 'Pima malaria kituo cha afya ndani ya saa 24. Kunywa maji mengi.'},
    'respiratory': {'en': 'Rest, drink fluids and cover coughs. Seek care if breathing gets harder.',
                    'sw': 'Pumzika, kunywa maji na funika mdomo ukikohoa. Tafuta matibabu ukishindwa kupumua.'},
    'diarrhoea': {'en': 'Drink ORS after every loose stool, give zinc to children, boil water and wash hands.',
                  'sw': 'Kunywa ORS kila unapoharisha, wape watoto zinki, chemsha maji na nawa mikono.'},
    'rash': {'en': 'Keep the sick person apart from others and visit a health facility. Check vaccinations.',
             'sw': 'Mtenge mgonjwa na wengine na nenda kituo cha afya. Hakikisha chanjo.'},
    'jaundice': {'en': 'Visit a health facility for a check. Drink only boiled or treated water.',
                 'sw': 'Nenda kituo cha afya kupimwa. Kunywa maji yaliyochemshwa au kutibiwa tu.'},
    'other': {'en': 'If it gets worse, visit the nearest health facility.',
              'sw': 'Ikizidi, nenda kituo cha afya kilicho karibu.'},
}

WEEKDAYS_SHORT = {
    'en': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    'sw': ['Jtatu', 'Jnne', 'Jtano', 'Alh', 'Ijumaa', 'Jmosi', 'Jpili'],
}


def t(key, lang='en', **values):
    entry = STRINGS[key]
    text = entry.get(lang) or entry['en']
    return text.format(**values) if values else text


def format_when(when, lang='en'):
    """'Tue 19/11 10:00' (short enough for a USSD line)."""
    day = WEEKDAYS_SHORT.get(lang, WEEKDAYS_SHORT['en'])[when.weekday()]
    return f"{day} {when.strftime('%d/%m %H:%M')}"
