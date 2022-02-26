from django.conf import settings  # import the settings file


def env_profile(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {'ENV': settings.ENV_PROFILE}
