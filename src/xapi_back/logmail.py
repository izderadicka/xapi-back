'''
Created on Feb 5, 2016

@author: ivan
'''
import logging
import smtplib
log = logging.getLogger('logmail')

class BufferingSMTPHandler(logging.handlers.BufferingHandler):
    def __init__(self, mailhost, mailport, fromaddr, toaddr, user='', password='', subject='', secure=False):
        logging.handlers.BufferingHandler.__init__(self, None)
        self.mailhost = mailhost
        self.mailport = mailport or (smtplib.SMTP_PORT if not secure else smtplib.SMTP_SSL_PORT)
        self.fromaddr = fromaddr
        self.toaddr = toaddr
        self.subject = subject
        self.user=user
        self.password=password
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
        self.secure=secure

    def shouldFlush(self, record):
        return False
    
    def flush(self):
        try:
            self.acquire()
            if len(self.buffer) > 0:
                header="From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (self.fromaddr, ','.join(self.toaddr), self.subject)
                msg= "\r\n".join(map(self.format, self.buffer))
                if self.secure:
                    smtp = smtplib.SMTP_SSL(self.mailhost, self.mailport)
                else:
                    smtp = smtplib.SMTP(self.mailhost, self.mailport)
                if self.user:
                    smtp.login(self.user, self.password)
                smtp.sendmail(self.fromaddr, self.toaddr, header+msg)
                log.debug('Succesfully sent mail to %s', self.toaddr)
                smtp.quit()
        except Exception:
            log.exception('Failed to send email to %s', self.toaddr)
        finally:
            self.buffer=[]
            self.release()