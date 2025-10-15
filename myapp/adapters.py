from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.urls import reverse


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to handle OAuth redirects properly
    """
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully
        connecting a social account.
        """
        return reverse('chatbot_page')
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after successfully
        logging in with a social account.
        """
        return reverse('chatbot_page')
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Checks whether or not the social signup is open for auto signup.
        """
        return True
    
    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login. In case of auto-signup,
        the signup form is not available.
        """
        user = sociallogin.user
        user.set_unusable_password()
        user.save()
        return user