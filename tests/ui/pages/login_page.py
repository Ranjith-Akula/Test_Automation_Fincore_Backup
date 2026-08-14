class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = page.get_by_test_id("login-username-input")
        self.password_input = page.get_by_test_id("login-password-input")
        self.login_button = page.get_by_test_id("login-submit-btn")
        self.error_message = page.get_by_test_id("login-error")
        self.logout_button = page.get_by_test_id("logout-button")

    def goto(self):
        self.page.goto("/login")

    def login(self, username, password):
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def submit_empty(self):
        self.login_button.click()

    def logout(self):
        self.logout_button.click()    

    def username_is_invalid(self):
        return self.page.evaluate(
        'document.querySelector(\'[data-testid="login-username-input"]\').validity.valid === false'
        )

    def password_is_invalid(self):
        return self.page.evaluate(
        'document.querySelector(\'[data-testid="login-password-input"]\').validity.valid === false'
        )