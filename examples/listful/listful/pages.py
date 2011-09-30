import wtforms as wt
from pangur import (map, registerForm, User, LoginException, LogoutException,
                    RedirectException, validateCredentials, createUser)

#Create a register form and a login form and register them for use in templates
@registerForm
class LoginForm(wt.Form):
    username = wt.TextField("Username", [wt.validators.Required()])
    password = wt.PasswordField("Password", [wt.validators.Required()])


@registerForm
class RegisterForm(wt.Form):
    newUsername = wt.TextField("Username", [wt.validators.Required()])
    newEmail = wt.TextField("Email Address", [wt.validators.Required(),
                                              wt.validators.Email()])
    newPassword = wt.PasswordField("Password", [wt.validators.Required(),
                                                wt.validators.Length(6)])


@map('/', 'login.html')
def loginPage(request):
    #if the user is logged in already, send them on their way
    if request.session.user:
        raise RedirectException('/lists')
    values = {}
    if request.method == 'POST':

        #user submitted the login form:
        if 'LoginForm' in request.form:
            f = request.forms.load('LoginForm')
            if f.validate():
                username = request.form['username']
                password = request.form['password']
                user = validateCredentials(request, username, password)
                if user:
                    raise LoginException(user.id, '/lists')
                else:
                    values["loginError"] = "Incorrect username or password."

        #user submitted the register form:
        elif 'RegisterForm' in request.form:
            values['showRegForm'] = True
            f = request.forms.load('RegisterForm')
            if f.validate():
                username = request.form['newUsername']
                password = request.form['newPassword']
                #check if the name is already taken
                if request.txn.query(User).filter_by(username=username).first():
                    values["regError"] = "That name is taken, try again."
                    return values
                else:
                    user = createUser(request, username, password)
                    request.txn.commit() # and assign user.id
                    raise LoginException(user.id, '/lists')
    return values


@map('/logout')
def logout(request):
    raise LogoutException('/')


map('/lists', 'lists.html', authRequired=True)

