import os
import base64
import traceback

import textwrap
import flask
import flask_mail
import hmac
import hashlib

# Given the application's secret key, and a democracy person identifier,
# returns a token suitable for emailing to them to authenticate themselves.
def sign_person_id(secret_key, person_id):
    digest = hmac.new(secret_key.encode('ascii'), str(person_id).encode('ascii'), hashlib.sha512).digest()
    signature_bytes = base64.urlsafe_b64encode(digest)
    signature = signature_bytes.decode("ascii").rstrip("=\n")
    return signature[0:16]

# Returns a URL that lets someone upload a CV
def generate_upload_url(secret_key, person_id):
    signature = sign_person_id(secret_key, person_id)
    link = flask.url_for("upload_cv_confirmed", person_id=person_id, signature=signature, _external=True)

    return link

# Make debug email if appropriate
def map_to_email(app, to_email):
    if "DEBUG_EMAIL" in app.config:
        to_email = app.config["DEBUG_EMAIL"]
        print("DEBUG_EMAIL", to_email)
    return to_email

# Confirmation they're a candidate who can upload a CV

UPLOAD_CV_MESSAGE = textwrap.dedent("""\
    Hi {name},

    Thanks for offering to share your Curriculum Vitae with your future
    constituents.

    Click the link below to confirm your email, then upload your CV.

    {link}

    Thanks for your help!

    Francis Irving
    Volunteer
    Democracy Club CVs
    (we were behind TheyWorkForYou)
""")

def send_upload_cv_confirmation(app, mail, person_id, to_email, to_name):
    to_email = map_to_email(app, to_email)

    link = generate_upload_url(app.secret_key, person_id)

    print("confirm candidate email: ", person_id, " ", to_email, "\n", link, sep='')
    f = open("last_confirm_url.txt", 'w')
    try:
        f.write(link) # for use in selenium_tests.js
    finally:
        f.close()

    body = UPLOAD_CV_MESSAGE.format(name=to_name, link=link)
    msg = flask_mail.Message(body=body,
            subject="Share your CV with voters using this link",
            sender=("Democracy Club CV", "cv@democracyclub.org.uk"),
            recipients=[(to_name, to_email)]
          )

    mail.send(msg)


CONSTITUENT_MAIL_MESSAGE = textwrap.dedent("""\
    This is a message from a voter in your constituency asking you to
    share your CV. Follow this link to do so:
    {link}

    -------------------------------------------------------------------

    {message}

    -------------------------------------------------------------------

    NOTE: You can write to this voter at {from_email}. Their postcode
    is {postcode}.

    To share your CV please go to:
    {link}
    A Word document or a PDF is perfect!
""")

def send_email_candidates(app, mail, candidates, from_email, postcode, subject, message):
    for candidate in candidates:

        person_id = candidate['id']
        to_email = candidate['email']
        to_name = candidate['name']

        to_email = map_to_email(app, to_email)

        link = generate_upload_url(app.secret_key, person_id)
        print("email candidate asking: ", person_id, " ", to_email, "\n", link, sep='')

        full_message = "Dear " + to_name + ", \n\n" + message.strip()

        body = CONSTITUENT_MAIL_MESSAGE.format(name=to_name, link=link,
            from_email=from_email, postcode=postcode, message=full_message
        )
        msg = flask_mail.Message(body=body,
                subject=subject.strip(),
                sender=("Democracy Club CV", "cv@democracyclub.org.uk"),
                recipients=[(to_name, to_email)]
              )

        mail.send(msg)


