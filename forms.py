from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    SelectField,
    DateField
)
from wtforms.validators import DataRequired, Email, Length


class RegisterForm(FlaskForm):

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=20)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )

    submit = SubmitField("Register")

class LoginForm(FlaskForm):

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Login")

class TaskForm(FlaskForm):

    title = StringField(
        "Title",
        validators=[DataRequired()]
    )

    description = TextAreaField("Description")

    priority = SelectField(
        "Priority",
        choices=[
            ("High", "High"),
            ("Medium", "Medium"),
            ("Low", "Low")
        ]
    )

    due_date = DateField(
        "Due Date",
        format="%Y-%m-%d"
    )

    submit = SubmitField("Save Task")