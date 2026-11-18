"""Static reference data: Kenyan regions/counties, specialties, symptom groups.

Names are kept short because a USSD screen holds about 160 characters.
"""

# Former provinces -> counties (all 47 counties).
REGIONS = [
    ('nairobi', {'en': 'Nairobi', 'sw': 'Nairobi'}, ['Nairobi']),
    ('central', {'en': 'Central', 'sw': 'Kati'},
     ['Kiambu', "Murang'a", 'Nyeri', 'Kirinyaga', 'Nyandarua']),
    ('coast', {'en': 'Coast', 'sw': 'Pwani'},
     ['Mombasa', 'Kwale', 'Kilifi', 'Tana River', 'Lamu', 'Taita-Taveta']),
    ('eastern', {'en': 'Eastern', 'sw': 'Mashariki'},
     ['Marsabit', 'Isiolo', 'Meru', 'Tharaka-Nithi', 'Embu', 'Kitui', 'Machakos', 'Makueni']),
    ('north_eastern', {'en': 'North Eastern', 'sw': 'Kaskazini Mashariki'},
     ['Garissa', 'Wajir', 'Mandera']),
    ('nyanza', {'en': 'Nyanza', 'sw': 'Nyanza'},
     ['Siaya', 'Kisumu', 'Homa Bay', 'Migori', 'Kisii', 'Nyamira']),
    ('rift_valley', {'en': 'Rift Valley', 'sw': 'Bonde la Ufa'},
     ['Turkana', 'West Pokot', 'Samburu', 'Trans-Nzoia', 'Uasin Gishu', 'Elgeyo-Marakwet',
      'Nandi', 'Baringo', 'Laikipia', 'Nakuru', 'Narok', 'Kajiado', 'Kericho', 'Bomet']),
    ('western', {'en': 'Western', 'sw': 'Magharibi'},
     ['Kakamega', 'Vihiga', 'Bungoma', 'Busia']),
]

COUNTIES = sorted(c for _, _, counties in REGIONS for c in counties)
COUNTY_REGION = {c: code for code, _, counties in REGIONS for c in counties}


def region_counties(region_code):
    for code, _, counties in REGIONS:
        if code == region_code:
            return counties
    return []


# Specialties in the words patients use, with the clinical name for staff.
SPECIALTIES = [
    ('dermatology', 'Dermatology', {'en': 'Skin', 'sw': 'Ngozi'}),
    ('gynaecology', 'Obstetrics & Gynaecology',
     {'en': "Women's health & pregnancy", 'sw': 'Afya ya wanawake na ujauzito'}),
    ('neurology', 'Neurology', {'en': 'Brain & nerves', 'sw': 'Ubongo na neva'}),
    ('paediatrics', 'Paediatrics', {'en': "Children's health", 'sw': 'Afya ya watoto'}),
    ('cardiology', 'Cardiology', {'en': 'Heart & blood pressure', 'sw': 'Moyo na presha'}),
    ('psychiatry', 'Psychiatry', {'en': 'Mental health', 'sw': 'Afya ya akili'}),
    ('ophthalmology', 'Ophthalmology', {'en': 'Eyes', 'sw': 'Macho'}),
    ('ent', 'Ear, Nose & Throat', {'en': 'Ear, nose & throat', 'sw': 'Masikio, pua na koo'}),
    ('orthopaedics', 'Orthopaedics', {'en': 'Bones & joints', 'sw': 'Mifupa na viungo'}),
    ('endocrinology', 'Endocrinology', {'en': 'Diabetes & hormones', 'sw': 'Kisukari na homoni'}),
]
SPECIALTY_NAMES = {code: clinical for code, clinical, _ in SPECIALTIES}
SPECIALTY_LABELS = {code: labels for code, _, labels in SPECIALTIES}

# Syndromic surveillance groups (what a community member can recognise).
# urgent=True means any report is a red flag on its own.
SYNDROMES = [
    ('fever', {'en': 'Fever', 'sw': 'Homa'}, False),
    ('respiratory', {'en': 'Cough / hard breathing', 'sw': 'Kikohozi / shida kupumua'}, False),
    ('diarrhoea', {'en': 'Diarrhoea / vomiting', 'sw': 'Kuhara / kutapika'}, False),
    ('rash', {'en': 'Rash with fever', 'sw': 'Upele na homa'}, False),
    ('jaundice', {'en': 'Yellow eyes / skin', 'sw': 'Macho / ngozi ya manjano'}, False),
    ('neuro', {'en': 'Stiff neck / confusion', 'sw': 'Shingo ngumu / kuchanganyikiwa'}, True),
    ('bleeding', {'en': 'Unusual bleeding', 'sw': 'Kutokwa damu isivyo kawaida'}, True),
    ('other', {'en': 'Other illness', 'sw': 'Ugonjwa mwingine'}, False),
]
SYNDROME_LABELS = {code: labels for code, labels, _ in SYNDROMES}
URGENT_SYNDROMES = {code for code, _, urgent in SYNDROMES if urgent}

# Conditions each syndrome commonly signals; shown to health officers.
SYNDROME_WATCH = {
    'fever': 'Malaria, typhoid',
    'respiratory': 'Influenza, COVID-19, TB, pneumonia',
    'diarrhoea': 'Cholera, dysentery, typhoid',
    'rash': 'Measles, rubella, mpox',
    'jaundice': 'Hepatitis A/E, yellow fever',
    'neuro': 'Meningitis, rabies',
    'bleeding': 'Viral haemorrhagic fevers (e.g. Marburg, Ebola), dengue',
    'other': 'Unclassified',
}

HOUSEHOLD_SIZES = [('1', 1), ('2', 2), ('3', 4)]  # menu option -> people counted

EMERGENCY_NUMBERS = [
    ('999 / 112', {'en': 'Police & ambulance', 'sw': 'Polisi na ambulensi'}),
    ('1199', {'en': 'Kenya Red Cross', 'sw': 'Shirika la Msalaba Mwekundu'}),
    ('1195', {'en': 'Gender violence helpline', 'sw': 'Msaada wa dhuluma za kijinsia'}),
]

LANGUAGES = [('en', 'English'), ('sw', 'Kiswahili')]
