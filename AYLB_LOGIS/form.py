"""Small template helpers used by the existing account pages."""

from markupsafe import Markup, escape


class Field:
    def __init__(self, name, value="", errors=None, input_type="text"):
        self.name = name
        self.data = value
        self.errors = errors or []
        self.input_type = input_type

    def __call__(self, **attrs):
        attributes = {"type": self.input_type, "name": self.name, "id": self.name, "value": self.data}
        attributes.update(attrs)
        rendered = " ".join(f'{key.replace("_", "-")}="{escape(value)}"' for key, value in attributes.items() if value is not None)
        return Markup(f"<input {rendered}>")


class Form:
    submit_label = "Submit"

    def __init__(self, values=None, errors=None):
        values = values or {}
        errors = errors or {}
        for name in self.fields:
            setattr(self, name, Field(name, values.get(name, ""), errors.get(name, []), self.types.get(name, "text")))
        self.submit = Field("submit", self.submit_label, input_type="submit")
        self.remember = Field("remember", "y", input_type="checkbox")

    def hidden_tag(self):
        return Markup("")


class RegistrationForm(Form):
    submit_label = "Sign Up"
    fields = ("username", "first_name", "last_name", "email", "mobile_no", "password", "confirm_password")
    types = {"email": "email", "password": "password", "confirm_password": "password"}


class LoginForm(Form):
    submit_label = "Login"
    fields = ("email", "password")
    types = {"email": "email", "password": "password"}
