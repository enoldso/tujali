from datetime import datetime

def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """Format a date time to a different format.
    
    Args:
        value: Can be a datetime object, timestamp (float), or string
        format: str format for the output
    """
    if value is None:
        return ""
    
    try:
        # If it's already a datetime object, format it
        if hasattr(value, 'strftime'):
            return value.strftime(format)
        
        # If it's a string representation of a number (timestamp)
        if isinstance(value, str) and value.replace('.', '', 1).isdigit():
            value = float(value)
        
        # If it's a timestamp (float or int)
        if isinstance(value, (float, int)) and value > 1000000000:  # Rough check for Unix timestamp
            try:
                dt = datetime.fromtimestamp(float(value))
                return dt.strftime(format)
            except (ValueError, TypeError, OSError):
                pass
        
        # If it's a string, try to parse it as a datetime
        if isinstance(value, str):
            try:
                # Try parsing common datetime formats
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
                    try:
                        dt = datetime.strptime(value, fmt)
                        return dt.strftime(format)
                    except ValueError:
                        continue
            except (ValueError, TypeError):
                pass
        
        # If all else fails, return the string representation
        return str(value)
        
    except Exception as e:
        # If anything goes wrong, return a placeholder or the original value
        return str(value)

def register_filters(app):
    """Register all custom template filters."""
    app.jinja_env.filters['datetimeformat'] = format_datetime
