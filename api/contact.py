from http.server import BaseHTTPRequestHandler
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            message = data.get('message', '').strip()

            if not name or not email or not message:
                self._respond(400, {'error': 'Missing required fields'})
                return

            # SendGrid経由でメール送信
            sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', '')
            to_email = os.environ.get('CONTACT_TO_EMAIL', '')

            if sendgrid_api_key:
                import urllib.request
                payload = {
                    'personalizations': [{
                        'to': [{'email': to_email}],
                        'subject': f'[ポートフォリオ お問い合わせ] {name}様より'
                    }],
                    'from': {'email': 'noreply@tomoi-app.com', 'name': 'Portfolio Contact'},
                    'reply_to': {'email': email, 'name': name},
                    'content': [{
                        'type': 'text/plain',
                        'value': f'お名前: {name}\nメールアドレス: {email}\n\nメッセージ:\n{message}'
                    }]
                }
                req = urllib.request.Request(
                    'https://api.sendgrid.com/v3/mail/send',
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        'Authorization': f'Bearer {sendgrid_api_key}',
                        'Content-Type': 'application/json'
                    },
                    method='POST'
                )
                with urllib.request.urlopen(req) as response:
                    if response.status in (200, 202):
                        self._respond(200, {'ok': True})
                    else:
                        self._respond(500, {'error': 'Failed to send email'})
            else:
                # 開発環境では標準出力に出力
                print(f"[Contact Form] From: {name} <{email}>\nMessage: {message}")
                self._respond(200, {'ok': True, 'dev': True})

        except Exception as e:
            print(f"Contact API error: {e}")
            self._respond(500, {'error': str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _respond(self, status_code, body):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode('utf-8'))
