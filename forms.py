from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,\
    TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, Optional


class ChangeUsernameForm(FlaskForm):
    new_username = StringField('New Username',
                               validators=[DataRequired(),
                                           Length(min=3, max=15)])

    submit = SubmitField('Change Username')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password',
                                 validators=[DataRequired(),
                                             Length(min=3, max=15)])
    new_password = PasswordField('New Password', validators=[DataRequired(),
                                                             Length(min=3,
                                                                    max=15)])
    confirm_new_password = PasswordField('Confirm New Password',
                                         validators=[DataRequired(),
                                                     Length(min=3, max=15)])
    submit = SubmitField('Change Password')
