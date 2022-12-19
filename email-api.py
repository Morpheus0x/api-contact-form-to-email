from flask import Flask, request, current_app, jsonify
import configparser
import smtplib
from email.message import EmailMessage
import requests
from flask_cors import CORS

# load the config values from the config file
config = configparser.ConfigParser()
config.read('config.ini')
config = config['EMAIL-API']

def run():

  app = Flask(__name__)
  CORS(app, resources={r"/api/*": {"origins": config['CORS_ORIGIN']}})

  # testing route for form
  #@app.route('/')
  #def form():
  #  return current_app.send_static_file('contact-form.html')

  # forward contact form via email
  @app.route('/api/contact', methods=['POST'])
  def contact():
    if config['TURNSTILE_ENABLED']:
      r = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        'secret': config['TURNSTILE_SECRET_KEY'],
        'response': request.form['cf-turnstile-response']
      })
      if not r.json()['success']:
        return jsonify({'error': 2, 'msg': 'Invalid captcha'}) , 400

    msg = EmailMessage()
    msg.set_content(request.form['message'])
    msg['Subject'] = request.form['message'][:35] + '...' # TODO: sanitize message to remove newlines and multiple spaces
    msg['From'] = f"{request.form['name']} <{config['EMAIL_SENDER']}>"
    msg['To'] = config['EMAIL_TARGET']
    msg['Reply-To'] = request.form['email']

    # send the email
    try:
      with smtplib.SMTP_SSL(config['SMTP_SERVER'], config['SMTP_PORT']) as smtp:
        smtp.login(config['SMTP_USERNAME'], config['SMTP_PASSWORD'])
        smtp.send_message(msg)
    except: # Exception as e:
      return jsonify({'error': 1, 'msg': 'Error sending mail'}), 400
    return jsonify({'error': 0, 'msg': 'Email sent successfully'}), 200

  return app