import unittest, hashlib, imaplib, email, os, time
from datetime import  datetime
from confg import app_config
from app import create_app, app_database
from app.email import send_mail



class EmailTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()
    
    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()


    def test_send_email(self):
        mail_subject = self.app.config['MAIL_TEST_SUBJECT'] + \
                            hashlib.md5(str(datetime.utcnow).encode('utf-8')).hexdigest()
        mail_to = os.environ.get('MAIL_SENDER')
        send_mail(mail_subject, mail_to, self.app.config['MAIL_TEST_TEMPLATE'])

        #givr some time for the celery worker to finish the ama_send_mail task
        time.sleep(5)

        imap4_obj = imaplib.IMAP4_SSL(self.app.config['MAIL_IMAP4_SERVER'])
        try:
            mail_sender = os.environ.get('MAIL_SENDER')
            mail_password = os.environ.get('MAIL_PASSWORD')
            imap4_obj.login(mail_sender, mail_password)
        except imaplib.IMAP4.error:
            self.assertTrue(1 == 0)

        ret_val, dont_care = imap4_obj.select()
        self.assertTrue(ret_val == 'OK')
        ret_val, mails_numbers = imap4_obj.search(None, "ALL")
        self.assertTrue(ret_val == 'OK')

        found_mail = 0
        for num in mails_numbers[0].split():
            ret_val, mail = imap4_obj.fetch(num, '(RFC822)')
            self.assertTrue(ret_val == 'OK')
            mail_data = email.message_from_bytes(mail[0][1])
            if mail_data['Subject'] == mail_subject:
                found_mail = 1
        self.assertTrue(found_mail == 1)