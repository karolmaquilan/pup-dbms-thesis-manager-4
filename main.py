import webapp2
import jinja2
import os
import logging
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb
import json
import csv
import re

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)

class User(ndb.Model):
    usr_email = ndb.StringProperty(indexed=True)
    usr_fname = ndb.StringProperty(indexed=True)
    usr_lname = ndb.StringProperty(indexed=True)
    usr_pnum = ndb.IntegerProperty()
    usr_date = ndb.DateTimeProperty(auto_now_add=True)
    usr_idtty = ndb.StringProperty(indexed=False)
    usr_authrty = ndb.StringProperty(indexed=False)

class Greeting(ndb.Model):
    """Guestbook used as comment section"""
    author = ndb.StructuredProperty(User)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class Thesis(ndb.Model):
    thesis_created_by = ndb.KeyProperty(kind='User')
    thesis_title = ndb.StringProperty(indexed=True)
    thesis_abstract = ndb.TextProperty()
    thesis_year = ndb.IntegerProperty()
    thesis_section = ndb.IntegerProperty()
    thesis_department_key = ndb.KeyProperty(kind='Department')
    thesis_student_keys = ndb.KeyProperty(kind='Student',repeated=True)
    thesis_adviser_key = ndb.KeyProperty(kind='Faculty')
    date = ndb.DateTimeProperty(auto_now_add=True)

class Faculty(ndb.Model):
    fac_ttle = ndb.StringProperty(indexed=True)
    fac_fname = ndb.StringProperty(indexed=True,default='')
    fac_mname = ndb.StringProperty(indexed=True)
    fac_lname = ndb.StringProperty(indexed=True,default='')
    fac_email = ndb.StringProperty(indexed=True)
    fac_pnum = ndb.StringProperty(indexed=True)
    fac_bdate = ndb.StringProperty()
    fac_pic = ndb.StringProperty(indexed=True)

    @classmethod
    def get_by_key(cls, keyname):
        try:
            return ndb.Key(cls, keyname).get()
        except Exception:
            return None

class Student(ndb.Model):
    stud_fname = ndb.StringProperty(indexed=True,default='')
    stud_mname = ndb.StringProperty(indexed=True,default='')
    stud_lname = ndb.StringProperty(indexed=True,default='')
    stud_email = ndb.StringProperty(indexed=True)
    stud_pnum = ndb.StringProperty(indexed=True)
    stud_snum = ndb.StringProperty(indexed=True)
    stud_bdate = ndb.StringProperty()
    stud_pic = ndb.StringProperty(indexed=True)
    stud_yrgrad = ndb.StringProperty(indexed=True)

class University(ndb.Model):
    univ_name = ndb.StringProperty(indexed=True)
    univ_add = ndb.StringProperty(indexed=True)
    univ_initl = ndb.StringProperty(indexed=True)

class College(ndb.Model):
    clge_name = ndb.StringProperty(indexed=True)
    clge_univkey = ndb.KeyProperty(indexed=True)

class Department(ndb.Model):
    dep_clgekey = ndb.KeyProperty(indexed=True)
    dep_name = ndb.StringProperty(indexed=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext
        }

        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/index.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');

class ThesisCreate(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext
        }
        template = JINJA_ENVIRONMENT.get_template('templates/thesis/thesis_create.html')
        self.response.write(template.render(template_data))

class ImportHandler(webapp2.RequestHandler):
    def post(self):

        if self.request.get('csv_name'):
            if self.request.get('csv_name').find('.csv') > 0:
                csvfile = self.request.get('csv_name')
            else:
                csvfile = False;
                error = 'file type error'
        else:
            csvfile = False;
            error = 'please import a file!'

        if csvfile:
            f = csv.reader(open(csvfile , 'r'),skipinitialspace=True)
            counter = 1
            for row in f:
                # logging.info(counter)
                thesis = Thesis()
                th = Thesis.query(Thesis.thesis_title == row[4]).fetch()
                # know if thesis title already in database
                if not th:
                    if len(row[7]) > 2:
                        adviser_name = row[7] # 'Rodolfo Talan'
                        x = adviser_name.split(' ')
                        adv_fname = x[0]
                        adv_lname = x[1]
                        adviser_keyname = adviser_name.strip().replace(' ', '').lower()
                        adviser = Faculty.get_by_key(adviser_keyname)
                        if adviser is None:
                            adviser = Faculty(key=ndb.Key(Faculty, adviser_keyname), fac_fname=adv_fname, fac_lname=adv_lname)
                            thesis.thesis_adviser_key = adviser.put()
                        else:
                            thesis.thesis_adviser_key = adviser.key
                    else:
                        adv_fname = 'Anonymous'
                        adviser = Faculty(fac_fname=adv_fname, fac_lname=adv_lname)
                        thesis.thesis_adviser_key = adviser.put()
                    
                    for i in range(8,13):
                        stud = Student()
                        if row[i]:
                            stud_name = row[i].title().split(' ')
                            size = len(stud_name)
                            if size >= 1:
                                stud.stud_fname = stud_name[0]
                            if size >= 2:
                                stud.stud_mname = stud_name[1]
                            if size >= 3:
                                stud.stud_lname = stud_name[2]
                            thesis.thesis_student_keys.append(stud.put())

                    university = University(univ_name = row[0])
                    university.put()
                    college = College(clge_name = row[1], clge_univkey = university.key)
                    college.put()
                    department = Department(dep_name = row[2], dep_clgekey = college.key)
                    thesis.thesis_department_key = department.put()

                    thesis.thesis_year = int(row[3])
                    thesis.thesis_title = row[4]
                    thesis.thesis_abstract = row[5]
                    thesis.thesis_section = int(row[6])

                    user = users.get_current_user()
                    user_key = ndb.Key('User',user.user_id())

                    thesis.thesis_created_by = user_key
                    thesis.put()

                    adv_fname = ''
                    adv_lname = ''
                    counter=counter+1
            self.response.write('CSV imported successfully')
        else:
            self.response.write(error)

class LoginPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template_data = {
            'login' : users.create_login_url(self.request.uri),
            'register' : users.create_login_url(self.request.uri)
        }
        if user:
            self.redirect('/register')
        else:
            template = JINJA_ENVIRONMENT.get_template('templates/user/login.html')
            self.response.write(template.render(template_data))

class RegisterPage(webapp2.RequestHandler):
    def get(self):
        loginUser = users.get_current_user()

        if loginUser:
            user_key = ndb.Key('User',loginUser.user_id())
            user = user_key.get()
            if user:
                self.redirect('/')
            else:
                template = JINJA_ENVIRONMENT.get_template('templates/user/register.html')
                logout_url = users.create_logout_url('/login')
                template_data = {
                    'logout_url' : logout_url
                }
                self.response.write(template.render(template_data))
                template_data 
        else:
            login_url = users.create_login_url('/register')
            self.redirect(login_url)

    def post(self):
        loginUser = users.get_current_user()
        fname = self.request.get('first_name').title()
        lname = self.request.get('last_name').title()
        pnum = int(self.request.get('phone_num'))
        email = loginUser.email()
        user_id = loginUser.user_id()

        u = User.query(User.usr_fname == fname).fetch()
        if u:
            for user in u:
                if user.usr_lname == lname:
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Name have already been taken',
                    }
                    self.response.out.write(json.dumps(response))
                    return


        faculty_email = Faculty.query(Faculty.fac_email == email).get()
        if faculty_email:
            authority = 'faculty'
        else:
            authority = 'reader'
        user = User(id = user_id, usr_email=email,usr_fname=fname,usr_lname = lname,usr_pnum = pnum,usr_authrty= authority)
        logging.info(authority)
        user.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))

class  DeleteThesis(webapp2.RequestHandler):
    def get(self,th_id):
        d = Thesis.get_by_id(int(th_id))
        for studs in d.thesis_student_keys:
            s = studs.get()
            s.key.delete()
        d.key.delete()
        self.response.write('Thesis Deleted')

class  DeleteStudent(webapp2.RequestHandler):
    def get(self,s_id):
        key_to_delete = ndb.Key('Student',int(s_id))
        th = Thesis.query(projection=[Thesis.thesis_student_keys]).fetch()
        for t in th:
            if key_to_delete in t.thesis_student_keys:
                thesis = t.key.get()
                idx = thesis.thesis_student_keys.index(key_to_delete)
                del thesis.thesis_student_keys[idx]
                thesis.put()
        s = key_to_delete.get()
        s.key.delete()
        self.response.write('Student Deleted')

class  DeleteFaculty(webapp2.RequestHandler):
    def get(self,f_id):
        if f_id.isdigit():
            key_to_delete = ndb.Key('Faculty',int(f_id))
        else:
            key_to_delete = ndb.Key('Faculty',f_id)
        th = Thesis.query(projection=[Thesis.thesis_adviser_key]).fetch()
        for t in th:
            if key_to_delete == t.thesis_adviser_key:
                thesis = t.key.get()
                thesis.thesis_adviser_key = None
                thesis.put()
        f = key_to_delete.get()
        f.key.delete()
        self.response.write('Faculty Deleted')

class  DeleteCollege(webapp2.RequestHandler):
    def get(self,c_id):
        c = College.get_by_id(int(c_id))
        d = Department.query(Department.dep_clgekey == c.key).get()
        if d:
            d.dep_clgekey = None
        d.put()
        c.key.delete()

        self.response.write('College Deleted')

class  DeleteUniversity(webapp2.RequestHandler):
    def get(self,u_id):
        u = University.get_by_id(int(u_id))
        c = College.query(College.clge_univkey == u.key).get()
        if c:
            c.clge_univkey = None
        c.put()
        u.key.delete()

        self.response.write('University Deleted')

class APIHandlerPage(webapp2.RequestHandler):
    def get(self):
        thesis_list = []
        if self.request.get('year').isdigit():
            filt_year = int(self.request.get('year'))
        else:
            filt_year = None
        filt_adviser = self.request.get('adviser')

        if filt_adviser:
            x = filt_adviser.split(' ')
            filt_adv_fname = x[0]
            f = Faculty.query(Faculty.fac_fname == filt_adv_fname).fetch()
            for faculty in f:
                filt_adv_key = faculty.key
        else:
            filt_adv_key = None

        filt_university = self.request.get('university')

        if filt_university:
            filt_univ = University.query(University.univ_name == filt_university).get()
            filt_col = College.query(College.clge_univkey == filt_univ.key).get()
            filt_dept = Department.query(Department.dep_clgekey == filt_col.key).get()
        else:
            filt_dept = None

        if filt_year and filt_university and filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_year == filt_year,Thesis.thesis_department_key == filt_dept.key,Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_year and filt_university:
            thesis = Thesis.query(Thesis.thesis_year == filt_year,Thesis.thesis_department_key == filt_dept.key).order(+Thesis.thesis_title).fetch()
        elif filt_year and filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_year == filt_year,Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_university and filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_department_key == filt_dept.key,Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_year:
            thesis = Thesis.query(Thesis.thesis_year == filt_year).order(+Thesis.thesis_title).fetch()
        elif filt_adv_key:
            thesis = Thesis.query(Thesis.thesis_adviser_key == filt_adv_key).order(+Thesis.thesis_title).fetch()
        elif filt_university:
            thesis = Thesis.query(Thesis.thesis_department_key == filt_dept.key).order(+Thesis.thesis_title).fetch()
        else:
            thesis = Thesis.query().order(+Thesis.thesis_title).fetch()

        for thes in thesis:
            d = ndb.Key('Department',thes.thesis_department_key.id())
            dept = d.get()
            dept_name = dept.dep_name
            
            c = ndb.Key('College',dept.dep_clgekey.id())
            col = c.get()
            col_name = col.clge_name

            u = ndb.Key('University',col.clge_univkey.id())
            univ = u.get()
            univ_name = univ.univ_name

            creator = thes.thesis_created_by.get()

            if thes.thesis_adviser_key:
                adv = thes.thesis_adviser_key.get()
                adv_fname = adv.fac_fname
                adv_lname = adv.fac_lname
            else:
                adv = None
                adv_fname = None
                adv_lname = None

            thesis_list.append({
                'self_id':thes.key.id(),
                'thesis_title':thes.thesis_title,
                'thesis_year':thes.thesis_year,
                'fac_fname':adv_fname,
                'fac_lname':adv_lname,
                'thesis_creator_fname':creator.usr_fname,
                'thesis_creator_lname':creator.usr_lname,
                })

        if thesis_list:
            response = {
                'status':'OK',
                'data':thesis_list
            }
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(response))
        else:
            response = {
                'status':'Error',
            }
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(response))

    def post(self):
        th = Thesis.query(Thesis.thesis_title == self.request.get('thesis_title')).fetch()
        thesis = Thesis()
        thesis.thesis_title = self.request.get('thesis_title')
        thesis.thesis_abstract = self.request.get('thesis_abstract')
        thesis.thesis_year = int(self.request.get('thesis_year'))
        thesis.thesis_section = int(self.request.get('thesis_section'))

        proponents = []
        if self.request.get('thesis_member1'):
            proponents.append(self.request.get('thesis_member1'))
        if self.request.get('thesis_member2'):
            proponents.append(self.request.get('thesis_member2'))
        if self.request.get('thesis_member3'):
            proponents.append(self.request.get('thesis_member3'))
        if self.request.get('thesis_membe4'):
            proponents.append(self.request.get('thesis_member4'))
        if self.request.get('thesis_member5'):
            proponents.append(self.request.get('thesis_member5'))

        adviser = self.request.get('thesis_adviser')
        univ = self.request.get('university')
        col = self.request.get('college')
        dept = self.request.get('department')

        if len(th) >= 1:
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'Cannot create thesis. Title may be already exist'
            }
            self.response.out.write(json.dumps(response))

        else:
            for i in range(0,len(proponents)):
                name = proponents[i].title().split(' ')
                size = len(name)
                s = Student()
                if size >= 1:
                    s.stud_fname = name[0]
                if size >= 2:
                    s.stud_mname = name[1]
                if size >= 3:
                    s.stud_lname = name[2]
                thesis.thesis_student_keys.append(s.put())

            if len(adviser) > 2:
                adviser_name = adviser
                x = adviser_name.title().split(' ')
                sizex = len(x)
                if sizex >= 1:
                    adv_fname = x[0]
                else:
                    adv_fname = None

                if sizex >= 2:
                    adv_midname = x[1]
                else:
                    adv_midname = None

                if sizex >= 3:
                    adv_lname = x[2]
                else:
                    adv_lname = None

                adviser_keyname = adviser_name.strip().replace(' ', '').lower()
                adv = Faculty.get_by_key(adviser_keyname)
                if adv is None:
                    adv = Faculty(key=ndb.Key(Faculty, adviser_keyname), fac_fname=adv_fname, fac_lname=adv_lname, fac_mname=adv_midname)
                    thesis.thesis_adviser_key = adv.put()
                else:
                    thesis.thesis_adviser_key = adv.key
            else:
                adv_fname = 'Anonymous'
                adv = Faculty(fac_fname=adv_fname, fac_lname=adv_lname)
                thesis.thesis_adviser_key = adv.put()


            university = University(univ_name = univ)
            university.put()
            college = College(clge_name = col, clge_univkey = university.key)
            college.put()
            department = Department(dep_name = dept, dep_clgekey = college.key)
            thesis.thesis_department_key = department.put()

            user = users.get_current_user()
            user_key = ndb.Key('User',user.user_id())

            thesis.thesis_created_by = user_key

            thesis.put()

            self.response.headers['Content-Type'] = 'application/json'
            response = {
            'status':'OK'
            }
            self.response.out.write(json.dumps(response))

class  ThesisEdit(webapp2.RequestHandler):
    def get(self,th_id):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'

        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        s = Thesis.get_by_id(int(th_id))
        d = ndb.Key('Department',s.thesis_department_key.id())
        dept = d.get()
        dept_name = dept.dep_name
        
        c = ndb.Key('College',dept.dep_clgekey.id())
        col = c.get()
        col_name = col.clge_name

        u = ndb.Key('University',col.clge_univkey.id())
        univ = u.get()
        univ_name = univ.univ_name

        if s.thesis_adviser_key:
            adv = s.thesis_adviser_key.get()
        else:
            adv = None

        studs = {}
        num_proponents = len(s.thesis_student_keys)
        for i in range(0,num_proponents):
            studs[i] = s.thesis_student_keys[i].get()

        ###code for related thesis#########
        #get keywords from thesis title
        keywords = re.sub('[^\w]', ' ', s.thesis_title).split()
        #words to be removed
        not_noun = ['is','and','for','s','are','in','on','of','if','with','as','a','for']
        for i in range(len(not_noun)):
            if not_noun[i] in keywords:
                keywords.remove(not_noun[i])
        i = 0
        template_data = {
            'university':univ_name,
            'college':col_name,
            'department':dept_name,
            'num_proponents':num_proponents,
            'thesis': s,
            'i':i,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'greetings':greetings,
            'adv': adv,
            'studs': studs,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'keywords':keywords
        }

        template = JINJA_ENVIRONMENT.get_template('templates/thesis/thesis_edit.html')
        self.response.write(template.render(template_data))

    def post(self,th_id):
        title = self.request.get('thesis_title')
        th = Thesis.query(Thesis.thesis_title == title).fetch()

        t_id = th_id.replace('thesis/edit/','')
        thesis = Thesis.get_by_id(int(t_id))

        if thesis.thesis_title.lower().replace(' ','') == title.lower().replace(' ',''):
            j = 0
        else:
            j = len(th)

        thesis.thesis_title = self.request.get('thesis_title')
        thesis.thesis_abstract = self.request.get('thesis_abstract')
        thesis.thesis_year = int(self.request.get('thesis_year'))
        thesis.thesis_section = int(self.request.get('thesis_section'))
        ##check if proponents in edit has value##
        proponents = []
        if self.request.get('thesis_member1'):
            proponents.append(self.request.get('thesis_member1'))
        if self.request.get('thesis_member2'):
            proponents.append(self.request.get('thesis_member2'))
        if self.request.get('thesis_member3'):
            proponents.append(self.request.get('thesis_member3'))
        if self.request.get('thesis_membe4'):
            proponents.append(self.request.get('thesis_member4'))
        if self.request.get('thesis_member5'):
            proponents.append(self.request.get('thesis_member5'))

        adviser = self.request.get('thesis_adviser')
        dept_name = self.request.get('department')
        col_name = self.request.get('college')
        univ_name = self.request.get('university')
        ##checks if the univ,dept,college is in database or not##
        d = Department.query(Department.dep_name == dept_name).fetch()
        if d:
            for dept_key in d:
                #department name in database
                if dept_key.key == thesis.thesis_department_key:
                    #same department no changes in input
                    dkey = thesis.thesis_department_key
                    d_entity = dkey.get()
                else:
                    #need to get the key of that dept in database
                    thesis.thesis_department_key = dept_key.key
                    dkey = dept_key.key
                    d_entity = dkey.get()
                    d_entity.dep_name = dept_name
        else:
            dp = Department()
            dp.dep_name = dept_name
            dkey = dp.put()
            d_entity = dkey.get()

        c =  College.query(College.clge_name == col_name).fetch()
        if c:
            for col_key in c:
                #college name in database
                if col_key.key == d_entity.dep_clgekey:
                    #same college no changes in input
                    ckey = d_entity.dep_clgekey
                    c_entity = ckey.get()
                else:
                    #need to get the key of that college in database
                    d_entity.dep_clgekey = col_key.key
                    ckey = col_key.key
                    c_entity = ckey.get()
                    c_entity.clge_name = col_name
        else:
            cl = College()
            cl.clge_name = col_name
            ckey = cl.put()
            c_entity = ckey.get()

        u =  University.query(University.univ_name == univ_name).fetch()
        if u:
            for univ_key in u:
                #college name in database
                if univ_key.key == c_entity.clge_univkey:
                    #same college no changes in input
                    ukey = c_entity.clge_univkey
                    u_entity = ukey.get()
                else:
                    #need to get the key of that college in database
                    c_entity.clge_univkey = univ_key.key
                    ukey = univ_key.key
                    u_entity = ukey.get()
                    u_entity.univ_name = univ_name

            d_entity.put()
            c_entity.put()
            u_entity.put()
        else:
            un = University()
            un.univ_name = univ_name
            ukey = un.put()

        un_get = ukey.get()
        cl_get = ckey.get()
        cl_get.clge_univkey = un_get.put()
        dp_get = dkey.get()
        dp_get.dep_clgekey = cl_get.put()
        thesis.thesis_department_key = dp_get.put()


        if j >= 1:
            self.response.headers['Content-Type'] = 'application/json'
            response = {
            'status':'Cannot create thesis. Title may be already exist'
            }
            self.response.out.write(json.dumps(response))

        else:
            for i in range(0,len(proponents)):
                name = proponents[i]
                x = name.title().split()
                sizex = len(x)

                if sizex >= 1:
                    first_name = x[0]
                else:
                    first_name = None
                if sizex >= 2:
                    middle_name = x[1]
                else:
                    middle_name = None
                if sizex >= 3:
                    last_name = x[2]
                else:
                    last_name = None

                s = Student.query(Student.stud_lname == last_name).fetch()
                in_query = False
                in_thesis_stud_key = False
                
                if s:
                    for student in s:
                        # if student in query and student.key is in thesis stud key
                        if student.stud_fname == first_name and student.stud_mname == middle_name:
                            in_query = True
                            if student.key in thesis.thesis_student_keys:
                                logging.info(student.stud_fname)
                                logging.info(student.stud_lname)
                                logging.info(student.stud_mname)
                                in_thesis_stud_key = True
                        # elif student in query and student key is not in thesis stud key
                        elif in_query and not in_thesis_stud_key:
                            thesis.thesis_student_keys[i] = student.key
                        # else student not in query
                        else:
                            s = Student()
                            if sizex >= 1:
                                s.stud_fname = first_name
                            if sizex >= 2:
                                s.stud_mname = middle_name
                            if sizex >= 3:
                                s.stud_lname = last_name
                            thesis.thesis_student_keys[i] = s.put()
                else:
                    s = Student()
                    if sizex >= 1:
                        s.stud_fname = first_name
                    if sizex >= 2:
                        s.stud_mname = middle_name
                    if sizex >= 3:
                        s.stud_lname = last_name
                    thesis.thesis_student_keys[i] = s.put()

            if len(adviser) > 2:
                adviser_name = adviser
                x = adviser_name.title().split(' ')
                sizex = len(x)
                if sizex >= 1:
                    adv_fname = x[0]
                else:
                    adv_fname = None

                if sizex >= 2:
                    adv_midname = x[1]
                else:
                    adv_midname = None

                if sizex >= 3:
                    adv_lname = x[2]
                else:
                    adv_lname = None

                adviser_keyname = adviser_name.strip().replace(' ', '').lower()
                adv = Faculty.get_by_key(adviser_keyname)
                if adv is None:
                    adv = Faculty(key=ndb.Key(Faculty, adviser_keyname), fac_fname=adv_fname, fac_lname=adv_lname, fac_mname=adv_midname)
                    thesis.thesis_adviser_key = adv.put()
                else:
                    thesis.thesis_adviser_key = adv.key
            else:
                adv_fname = 'Anonymous'
                adv = Faculty(fac_fname=adv_fname, fac_lname=adv_lname)
                thesis.thesis_adviser_key = adv.put()

            thesis.put()

            self.response.headers['Content-Type'] = 'application/json'
            response = {
            'status':'OK'
            }
            self.response.out.write(json.dumps(response))

class RelatedThesAPI(webapp2.RequestHandler):
    def post(self):
        obj = json.loads(self.request.body)
        #get thesis titles
        related = {}
        rel_words = {}

        t = Thesis.query().order(+Thesis.thesis_title).fetch()
        for titles in t:
            #see if keywords is in each titles
            for i in range(len(obj['keywords'])):
                if obj['x'] != titles.thesis_title:
                    if obj['keywords'][i] in titles.thesis_title:
                        #know if the u got the whole exact word by seeing if it have spaces both ends
                        start_index = titles.thesis_title.find(obj['keywords'][i])
                        end_index = start_index + len(obj['keywords'][i]) - 1
                        if start_index != 0 and end_index != len(titles.thesis_title) - 1:
                            # logging.info(str(start_index)+" "+str(end_index)+ " "+str(len(titles.thesis_title) - 1))
                            if titles.thesis_title[end_index + 1] == " " and titles.thesis_title[start_index - 1] == " ":
                                #get thesis univ,college,dept,title,year,id

                                d = ndb.Key('Department',titles.thesis_department_key.id())
                                dept = d.get()
                                dept_name = dept.dep_name
                                
                                c = ndb.Key('College',dept.dep_clgekey.id())
                                col = c.get()
                                col_name = col.clge_name

                                u = ndb.Key('University',col.clge_univkey.id())
                                univ = u.get()
                                univ_name = univ.univ_name

                                related[titles.thesis_title] = {
                                    'thesis_title':titles.thesis_title,
                                    'thesis_university':univ_name,
                                    'thesis_college':col_name,
                                    'thesis_department':dept_name,
                                    'thesis_year':titles.thesis_year,
                                    'id':titles.key.id()
                                }
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
            'rel':related
        }
        self.response.out.write(json.dumps(response)) 

class SearcherAPI(webapp2.RequestHandler):
    def post(self):
        obj = json.loads(self.request.body)
        t = Thesis.query().order(+Thesis.thesis_title).fetch()
        s = Student.query().order(+Student.stud_fname).fetch()
        searched = {}
        for titles in t:
            ##see if keyword is in title name##
            if titles.thesis_title.lower().find(obj['y']) != -1:
                d = ndb.Key('Department',titles.thesis_department_key.id())
                dept = d.get()
                dept_name = dept.dep_name
                
                c = ndb.Key('College',dept.dep_clgekey.id())
                col = c.get()
                col_name = col.clge_name

                u = ndb.Key('University',col.clge_univkey.id())
                univ = u.get()
                univ_name = univ.univ_name

                searched[titles.thesis_title] = {
                                    'thesis_title':titles.thesis_title,
                                    'university':univ_name,
                                    'college':col_name,
                                    'department':dept_name,
                                    'thesis_year':titles.thesis_year,
                                    'id':titles.key.id()
                                }
        ##if thesis got none after search then search for student
        if searched == {}:
            for student in s:
                if student.stud_fname.lower().find(obj['y']) != -1 or student.stud_mname.lower().find(obj['y']) != -1 or student.stud_lname.lower().find(obj['y']) != -1:
                    searched[student.stud_fname] = {
                                    'student.stud_fname':student.stud_fname,
                                    'student.stud_mname':student.stud_mname,
                                    'student.stud_lname':student.stud_lname,
                                    'id':student.key.id()
                                }
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
            'searched':searched
        }
        self.response.out.write(json.dumps(response))

class StudentPage(webapp2.RequestHandler):
    def get(self,s_id):
        s = Student.get_by_id(int(s_id))
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'student': s,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/student/student_profile.html')
        self.response.write(template.render(template_data))
    def post(self,s_id):
        s = Student.get_by_id(int(s_id))
        s.stud_fname = self.request.get('stud_fname')
        s.stud_mname = self.request.get('stud_mname')
        s.stud_lname = self.request.get('stud_lname')
        s.stud_email = self.request.get('stud_email')
        s.stud_pnum = self.request.get('stud_pnum')
        s.stud_snum = self.request.get('stud_snum')
        s.stud_bdate = self.request.get('stud_bdate')
        s.stud_yrgrad = self.request.get('stud_yrgrad')
        s.stud_pic = self.request.get('stud_pic')
        s.put()
        self.redirect('/')

class FacultyPage(webapp2.RequestHandler):
    def get(self,f_id):
        if f_id.isdigit():
            f = Faculty.get_by_id(int(f_id))
        else:
            f = Faculty.get_by_id(f_id)
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'faculty': f,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('/templates/faculty/faculty_profile.html')
        self.response.write(template.render(template_data))
    def post(self,f_id):
        f = Faculty.get_by_id(f_id)
        f.fac_fname = self.request.get('fac_fname')
        f.fac_mname = self.request.get('fac_mname')
        f.fac_lname = self.request.get('fac_lname')
        f.fac_email = self.request.get('fac_email')
        f.fac_pnum = self.request.get('fac_pnum')
        f.fac_bdate = self.request.get('fac_bdate')
        f.fac_pic = self.request.get('fac_pic')
        f.fac_ttle = self.request.get('fac_ttle')
        f.put() 
        self.redirect('/')
class UniversityPage(webapp2.RequestHandler):
    def get(self,u_id):
        u = University.get_by_id(int(u_id))
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'university': u,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('/templates/university/university_profile.html')
        self.response.write(template.render(template_data))
    def post(self,u_id):
        u = University.get_by_id(int(u_id))
        u.univ_name = self.request.get('univ_name')
        u.univ_initl = self.request.get('univ_initl')
        u.univ_add = self.request.get('univ_add')
        u.put() 
        self.redirect('/')

class CollegePage(webapp2.RequestHandler):
    def get(self,c_id):
        c = College.get_by_id(int(c_id))
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'college': c,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('/templates/college/college_profile.html')
        self.response.write(template.render(template_data))
    def post(self,c_id):
        c = College.get_by_id(int(c_id))
        c.clge_name = self.request.get('clge_name')
        c.put()
        self.redirect('/')

class ThesisList(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        universities = []
        f = Faculty.query(projection=[Faculty.fac_fname,Faculty.fac_lname]).order(+Faculty.fac_lname).fetch()
        u = University.query(projection=[University.univ_name]).order(+University.univ_name).fetch()
        for univ in u:
            if univ.univ_name not in universities:
                universities.append(univ.univ_name)
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
            'faculty':f,
            'universities':universities
        }
        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/thesis/thesis_list.html')
            self.response.write(template.render(template_data))
        else:
            self.redirect('/login');
class CreateFaculty(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/faculty/faculty_create.html')
        self.response.write(template.render(template_data))
    def post(self):
        obj = json.loads(self.request.body)
        first_name = obj['faculty_data']['fac_fname']
        middle_name = obj['faculty_data']['fac_mname']
        last_name = obj['faculty_data']['fac_lname']

        adviser_name = first_name + " " + middle_name + " " + last_name
        x = adviser_name.title().split()
        sizex = len(x)
        if sizex >= 1:
            adv_fname = x[0]
        else:
            adv_fname = None

        if sizex >= 2:
            adv_midname = x[1]
        else:
            adv_midname = None

        if sizex >= 3:
            adv_lname = x[2]
        else:
            adv_lname = None

        adviser_keyname = adviser_name.strip().replace(' ','').lower()
        adv = Faculty.get_by_key(adviser_keyname)
        if adv is None:
            adv = Faculty(key=ndb.Key(Faculty, adviser_keyname), fac_fname=adv_fname, fac_lname=adv_lname, fac_mname=adv_midname,\
                fac_email=obj['faculty_data']['fac_email'],fac_pnum=obj['faculty_data']['fac_pnum'],fac_bdate=obj['faculty_data']['fac_bdate'],\
                fac_pic=obj['pic_path'])
            adv.put()
            for i in range(len(obj['thesis'])):
                t = Thesis.query(Thesis.thesis_title == obj['thesis'][i]).fetch()
                if t[0].thesis_adviser_key is None:
                    t[0].thesis_adviser_key = adv.key
                    t[0].put()

                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'OK',
                    }
                    self.response.out.write(json.dumps(response))
                    return
                else:
                    adv.key.delete()
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Some thesis already have an adviser',
                    }
                    self.response.out.write(json.dumps(response))
                    return
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'OK',
            }
            self.response.out.write(json.dumps(response))
        else:
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'Faculty already exist!',
            }
            self.response.out.write(json.dumps(response))

class CreateStudent(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/student/student_create.html')
        self.response.write(template.render(template_data))
    def post(self):
        obj = json.loads(self.request.body)
        name = obj['student_data']['stud_fname'] + " " + obj['student_data']['stud_mname'] + " " + obj['student_data']['stud_lname']
        x = name.title().split()
        sizex = len(x)

        if sizex >= 1:
            first_name = x[0]
        else:
            first_name = None
        if sizex >= 2:
            middle_name = x[1]
        else:
            middle_name = None
        if sizex >= 3:
            last_name = x[2]
        else:
            last_name = None

        s = Student.query(Student.stud_lname == last_name).fetch()

        if s:
            for student in s:
                if student.stud_fname == first_name and student.stud_mname == middle_name:
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Student already exist!',
                    }
                    self.response.out.write(json.dumps(response))
                    return
                else:
                    stud = Student()
                    stud.stud_fname = first_name
                    stud.stud_mname = middle_name
                    stud.stud_lname = last_name

                    stud.stud_email = obj['student_data']['stud_email']
                    stud.stud_pnum = obj['student_data']['stud_pnum']
                    stud.stud_snum = obj['student_data']['stud_snum']
                    stud.stud_bdate = obj['student_data']['stud_bdate']
                    stud.stud_yrgrad = obj['student_data']['stud_yrgrad']
                    stud.stud_pic = obj['pic_path']
                    stud.put()
                    for i in range(len(obj['thesis'])):
                        t = Thesis.query(Thesis.thesis_title == obj['thesis'][i]).fetch()
                        if len(t[0].thesis_student_keys) < 5:
                            t[0].thesis_student_keys.append(stud.key)
                            t[0].put()
                            self.response.headers['Content-Type'] = 'application/json'
                            response = {
                                'status':'OK',
                            }
                            self.response.out.write(json.dumps(response))
                            return
                        else:
                            self.response.headers['Content-Type'] = 'application/json'
                            response = {
                                'status':'Maximum student in thesis',
                            }
                            self.response.out.write(json.dumps(response))
                            return
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'OK',
                    }
                    self.response.out.write(json.dumps(response))
        else:
            stud = Student()
            stud.stud_fname = first_name
            stud.stud_mname = middle_name
            stud.stud_lname = last_name

            stud.stud_email = obj['student_data']['stud_email']
            stud.stud_pnum = obj['student_data']['stud_pnum']
            stud.stud_snum = obj['student_data']['stud_snum']
            stud.stud_bdate = obj['student_data']['stud_bdate']
            stud.stud_yrgrad = obj['student_data']['stud_yrgrad']
            stud.stud_pic = obj['pic_path']
            stud.put()
            for i in range(len(obj['thesis'])):
                t = Thesis.query(Thesis.thesis_title == obj['thesis'][i]).fetch()
                if len(t[0].thesis_student_keys) < 5:
                    t[0].thesis_student_keys.append(stud.key)
                    t[0].put()
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'OK',
                    }
                    self.response.out.write(json.dumps(response))
                else:
                    self.response.headers['Content-Type'] = 'application/json'
                    response = {
                        'status':'Maximum student in thesis',
                    }
                    self.response.out.write(json.dumps(response))
            self.response.headers['Content-Type'] = 'application/json'
            response = {
                'status':'OK',
            }
            self.response.out.write(json.dumps(response))

class CreateUniversity(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/university/university_create.html')
        self.response.write(template.render(template_data))
    def post(self):
        name = self.request.get('university_name')
        lower = name.lower().replace(' ', '')
        u = University.query().order(+University.univ_name).fetch()
        for univ in u:
            if univ.univ_name.lower().replace(' ', '') == lower:
                self.response.headers['Content-Type'] = 'application/json'
                response = {
                    'status':'University already exist.',
                }
                self.response.out.write(json.dumps(response))
                return
        univ = University()
        univ.univ_name = name
        univ.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))


class CreateCollege(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/college/college_create.html')
        self.response.write(template.render(template_data))
    def post(self):
        name = self.request.get('college_name')
        lower = name.lower().replace(' ', '')
        c = College.query().order(+College.clge_name).fetch()
        for col in c:
            if col.clge_name.lower().replace(' ', '') == lower:
                self.response.headers['Content-Type'] = 'application/json'
                response = {
                    'status':'College already exist.',
                }
                self.response.out.write(json.dumps(response))
                return
        college = College()
        college.clge_name = name
        college.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))

class CreateDepartment(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        template_data = {
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/department/department_create.html')
        self.response.write(template.render(template_data))
    def post(self):
        name = self.request.get('department_name')
        lower = name.lower().replace(' ', '')
        d = Department.query().order(+Department.dep_name).fetch()
        for dept in d:
            if dept.dep_name.lower().replace(' ', '') == lower:
                self.response.headers['Content-Type'] = 'application/json'
                response = {
                    'status':'Department already exist.',
                }
                self.response.out.write(json.dumps(response))
                return
        dpt = Department()
        dpt.dep_name = name
        dpt.put()
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
        }
        self.response.out.write(json.dumps(response))

class ListFaculty(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        f = Faculty.query().order(+Faculty.fac_lname).fetch()
        template_data = {
            'faculty':f,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/faculty/faculty_list.html')
        self.response.write(template.render(template_data))

class ListStudent(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        s = Student.query().order(+Student.stud_lname).fetch()
        template_data = {
            'student':s,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/student/student_list.html')
        self.response.write(template.render(template_data))

class ListUniversity(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        u = University.query().order(+University.univ_name).fetch()
        template_data = {
            'university':u,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/university/university_list.html')
        self.response.write(template.render(template_data))

class ListCollege(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        c = College.query().order(+College.clge_name).fetch()
        template_data = {
            'college':c,
            'user': user,
            'url': url,
            'url_linktext': url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('templates/college/college_list.html')
        self.response.write(template.render(template_data))

class APIThesisFinder(webapp2.RequestHandler):
    def get(self):
        title = self.request.get('title')
        t = Thesis.query().order(+Thesis.thesis_title).fetch()
        finder = {}
        for titles in t:
            if titles.thesis_title.lower().find(title) != -1:
                finder[titles.thesis_title] = {'thesis_title':titles.thesis_title}
        self.response.headers['Content-Type'] = 'application/json'
        response = {
            'status':'OK',
            'finder':finder
        }
        self.response.out.write(json.dumps(response))

class Guestbook(webapp2.RequestHandler):
    def post(self):
        url_id = self.request.get('thesis_id')
        logging.info(url_id)
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))
        if users.get_current_user():
            greeting.author = User(
                    usr_idtty=users.get_current_user().user_id(),
                    usr_email=users.get_current_user().email())
        greeting.content = self.request.get('content')
        greeting.put()
        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/thesis/edit/'+url_id+'?' + urllib.urlencode(query_params))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login',LoginPage),
    ('/register',RegisterPage),
    ('/api/handler', APIHandlerPage),
    ('/api/find_thesis', APIThesisFinder),
    ('/api/getRelated', RelatedThesAPI),
    ('/api/searcher', SearcherAPI),
    ('/thesis/delete/(.*)', DeleteThesis),
    ('/student/delete/(.*)', DeleteStudent),
    ('/faculty/delete/(.*)', DeleteFaculty),
    ('/college/delete/(.*)', DeleteCollege),
    ('/university/delete/(.*)', DeleteUniversity),
    ('/faculty/list', ListFaculty),
    ('/student/list', ListStudent),
    ('/university/list', ListUniversity),
    ('/college/list', ListCollege),
    ('/faculty/create', CreateFaculty),
    ('/student/create', CreateStudent),
    ('/university/create', CreateUniversity),
    ('/college/create', CreateCollege),
    ('/department/create', CreateDepartment),
    ('/thesis/list', ThesisList),
    ('/thesis/edit/(.*)', ThesisEdit),
    ('/thesis/create', ThesisCreate),
    ('/student/page/(.*)', StudentPage),
    ('/faculty/page/(.*)',FacultyPage),
    ('/university/page/(.*)',UniversityPage),
    ('/college/page/(.*)',CollegePage),
    ('/csvimport', ImportHandler),
    ('/sign', Guestbook)
], debug=True)