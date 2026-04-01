class LinkVisitorUserInfo:

    def __init__(self, user_id: str, user_pw: str, **kwargs):
        self.user_id = user_id
        self.user_pw = user_pw
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"LinkVisitorUserInfo(user_id={self.user_id}, user_pw={self.user_pw})"
