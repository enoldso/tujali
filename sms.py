"""Outbound SMS.

Backends (SMS_BACKEND):
- "console" (default): messages are stored in sms_messages with status
  "logged" and written to the log. Nothing leaves the server.
- "africastalking": sent through Africa's Talking. Needs AT_USERNAME and
  AT_API_KEY; AT_SENDER_ID is optional. Use AT_USERNAME=sandbox to test.

Every message is recorded in the sms_messages table either way.
"""
import json
import logging
import urllib.parse
import urllib.request

from flask import current_app

from models import db, SmsMessage

logger = logging.getLogger(__name__)

MAX_LENGTH = 480  # three SMS segments


def send_sms(phone, body, purpose=None, commit=True):
    body = body.strip()[:MAX_LENGTH]
    message = SmsMessage(phone=phone, body=body, purpose=purpose)
    backend = current_app.config.get('SMS_BACKEND', 'console')

    if backend == 'africastalking':
        try:
            message.provider_ref = _send_africastalking(phone, body)
            message.status = 'sent'
        except Exception as exc:  # network errors, bad credentials, rejected number
            logger.exception('SMS to %s failed', mask_phone(phone))
            message.status = 'failed'
            message.error = str(exc)[:255]
    else:
        logger.info('SMS (console) to %s [%s]: %s', mask_phone(phone), purpose, body)
        message.status = 'logged'

    db.session.add(message)
    if commit:
        db.session.commit()
    return message


def _send_africastalking(phone, body):
    config = current_app.config
    username = config['AT_USERNAME']
    host = 'api.sandbox.africastalking.com' if username == 'sandbox' else 'api.africastalking.com'
    payload = {'username': username, 'to': phone, 'message': body}
    if config.get('AT_SENDER_ID'):
        payload['from'] = config['AT_SENDER_ID']

    request = urllib.request.Request(
        f'https://{host}/version1/messaging',
        data=urllib.parse.urlencode(payload).encode(),
        headers={'apiKey': config['AT_API_KEY'], 'Accept': 'application/json',
                 'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST')
    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode())

    recipients = data.get('SMSMessageData', {}).get('Recipients', [])
    if not recipients or recipients[0].get('status') not in ('Success', 'Sent'):
        raise RuntimeError(f"Africa's Talking rejected the message: {data}")
    return recipients[0].get('messageId')


def mask_phone(phone):
    return phone[:-4] + '****' if phone and len(phone) > 6 else '****'
