
class HighlightMedia:
    """
    Utility class to provide Highlight.js assets to the admin.
    """
    css = {
        'all': ('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/stackoverflow-light.min.css',)
    }
    js = (
        'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
        'js/admin_highlight_init.js',
    )