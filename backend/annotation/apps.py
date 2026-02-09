from django.apps import AppConfig


class AnnotationConfig(AppConfig):
    name = 'annotation'

    def ready(self):
        import annotation.signals
