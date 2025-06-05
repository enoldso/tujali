from datetime import datetime

def format_date(date_str, language='en'):
    """
    Format a date string to be more user-friendly
    
    Args:
        date_str (str): Date string in format DD-MM-YYYY
        language (str): Language code ('en' or 'sw')
    
    Returns:
        str: Formatted date string
    """
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        
        # Format based on language
        if language == 'en':
            # English format (e.g., "Mon, 12 Jun 2023")
            weekday = date_obj.strftime('%a')
            day = date_obj.strftime('%d')
            month = date_obj.strftime('%b')
            year = date_obj.strftime('%Y')
            return f"{weekday}, {day} {month} {year}"
        else:
            # Swahili format
            weekday_map = {
                'Mon': 'Jumatatu',
                'Tue': 'Jumanne',
                'Wed': 'Jumatano',
                'Thu': 'Alhamisi',
                'Fri': 'Ijumaa',
                'Sat': 'Jumamosi',
                'Sun': 'Jumapili'
            }
            
            month_map = {
                'Jan': 'Januari',
                'Feb': 'Februari',
                'Mar': 'Machi',
                'Apr': 'Aprili',
                'May': 'Mei',
                'Jun': 'Juni',
                'Jul': 'Julai',
                'Aug': 'Agosti',
                'Sep': 'Septemba',
                'Oct': 'Oktoba',
                'Nov': 'Novemba',
                'Dec': 'Desemba'
            }
            
            weekday = weekday_map.get(date_obj.strftime('%a'), date_obj.strftime('%a'))
            day = date_obj.strftime('%d')
            month = month_map.get(date_obj.strftime('%b'), date_obj.strftime('%b'))
            year = date_obj.strftime('%Y')
            return f"{weekday}, {day} {month} {year}"
    except ValueError:
        # If there's an error parsing the date, return it as is
        return date_str
